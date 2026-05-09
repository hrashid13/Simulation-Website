import { useState } from 'react'
import ConfigScreen from './components/ConfigScreen'
import LoadingScreen from './components/LoadingScreen'
import ReportScreen from './components/ReportScreen'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [screen, setScreen] = useState('config')
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

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

  if (screen === 'loading') return <LoadingScreen days={days} />
  if (screen === 'report') return <ReportScreen data={data} days={days} onReset={reset} />
  return <ConfigScreen onRun={runSimulation} error={error} />
}
