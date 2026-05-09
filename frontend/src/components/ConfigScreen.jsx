import { useState } from 'react'
import './ConfigScreen.css'

export default function ConfigScreen({ onRun, error }) {
  const [days, setDays] = useState(30)
  const [touched, setTouched] = useState(false)

  const valid = Number.isInteger(Number(days)) && days >= 1 && days <= 365

  function handleSubmit(e) {
    e.preventDefault()
    if (valid) onRun(Number(days))
  }

  return (
    <div className="config-page">
      <div className="config-card">
        <div className="config-icon">🎡</div>
        <h1 className="config-title">Amusement Park Simulator</h1>
        <p className="config-subtitle">
          Generate a fully randomized operational report for your park.
          Choose how many days to simulate, then let the engine run.
        </p>

        <form onSubmit={handleSubmit} className="config-form">
          <label className="config-label" htmlFor="days-input">
            Number of days to simulate
          </label>
          <input
            id="days-input"
            className={`config-input${touched && !valid ? ' config-input--error' : ''}`}
            type="number"
            min={1}
            max={365}
            value={days}
            onChange={e => { setDays(e.target.value); setTouched(true) }}
            onBlur={() => setTouched(true)}
          />
          {touched && !valid && (
            <p className="config-hint config-hint--error">Enter a whole number between 1 and 365.</p>
          )}
          {(!touched || valid) && (
            <p className="config-hint">Suggested range: 1 – 365 days</p>
          )}

          <div className="config-presets">
            {[7, 30, 90, 180, 365].map(n => (
              <button
                key={n}
                type="button"
                className={`preset-btn${Number(days) === n ? ' preset-btn--active' : ''}`}
                onClick={() => { setDays(n); setTouched(false) }}
              >
                {n}d
              </button>
            ))}
          </div>

          <button className="run-btn" type="submit" disabled={!valid}>
            Run Simulation
          </button>
        </form>

        {error && (
          <div className="config-error">
            <strong>Simulation failed:</strong> {error}
          </div>
        )}

        <div className="config-stats">
          <div className="stat-chip">7 rides</div>
          <div className="stat-chip">12 stores</div>
          <div className="stat-chip">6 archetypes</div>
          <div className="stat-chip">3 weather states</div>
        </div>
      </div>
    </div>
  )
}
