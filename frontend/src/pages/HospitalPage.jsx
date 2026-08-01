import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import HospitalConfigScreen from '../components/HospitalConfigScreen'
import LoadingScreen from '../components/LoadingScreen'
import HospitalReportScreen from '../components/HospitalReportScreen'
import Footer from '../components/Footer'
import './HospitalPage.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const LOADING_STEPS = [
  'Rolling daily event types...',
  'Generating patient arrivals...',
  'Triaging to ESI 1-5...',
  'Routing through departments...',
  'Working queues and bed capacity...',
  'Tracking complications and readmissions...',
  'Building your report...',
]

export default function HospitalPage() {
  const navigate = useNavigate()
  const [screen, setScreen] = useState('config')
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    document.title = 'Hospital Simulation — Simuleras'
    return () => { document.title = 'Simuleras' }
  }, [])

  async function runSimulation(numDays, forceMassCasualty) {
    setDays(numDays)
    setError(null)
    setScreen('loading')
    try {
      const res = await fetch(`${API_BASE}/simulate/hospital`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: numDays, force_mass_casualty: forceMassCasualty }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || `Server error ${res.status}`)
      }
      setData(await res.json())
      setScreen('report')
    } catch (err) {
      setError(err.message)
      setScreen('config')
    }
  }

  function reset() {
    // Dropping the result is the whole retention policy: nothing is cached and
    // nothing is persisted, so a new run means a genuinely new randomised seed.
    setData(null)
    setError(null)
    setScreen('config')
  }

  if (screen === 'report') {
    return (
      <HospitalReportScreen
        data={data}
        days={days}
        onReset={reset}
        onHome={() => navigate('/')}
      />
    )
  }

  return (
    <div className="hospital-page">
      <div className="hospital-back-bar">
        <button className="hospital-back-btn" onClick={() => navigate('/')}>
          Back to Simuleras
        </button>
      </div>

      {screen === 'loading'
        ? <LoadingScreen days={days} steps={LOADING_STEPS} />
        : <HospitalConfigScreen onRun={runSimulation} error={error} />
      }

      <Footer />
    </div>
  )
}
