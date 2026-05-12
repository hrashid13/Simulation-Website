import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ConfigScreen from '../components/ConfigScreen'
import LoadingScreen from '../components/LoadingScreen'
import ReportScreen from '../components/ReportScreen'
import Footer from '../components/Footer'
import './AmusementParkPage.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AmusementParkPage() {
  const navigate = useNavigate()
  const [screen, setScreen] = useState('config')
  const [days, setDays] = useState(90)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    document.title = 'Amusement Park Simulation — Simuleras'
    return () => { document.title = 'Simuleras' }
  }, [])

  async function runSimulation(numDays) {
    setDays(numDays)
    setError(null)
    setScreen('loading')
    try {
      const res = await fetch(`${API_BASE}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: numDays }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail.detail || `Server error ${res.status}`)
      }
      const result = await res.json()
      setData(result)
      setScreen('report')
    } catch (err) {
      setError(err.message)
      setScreen('config')
    }
  }

  function reset() {
    setData(null)
    setError(null)
    setScreen('config')
  }

  if (screen === 'report') {
    return <ReportScreen data={data} days={days} onReset={reset} onHome={() => navigate('/')} />
  }

  return (
    <div className="park-page">
      <div className="park-back-bar">
        <button className="park-back-btn" onClick={() => navigate('/')}>
          ← Back to Simuleras
        </button>
      </div>

      {screen === 'loading'
        ? <LoadingScreen days={days} />
        : <ConfigScreen onRun={runSimulation} error={error} />
      }

      <Footer />
    </div>
  )
}
