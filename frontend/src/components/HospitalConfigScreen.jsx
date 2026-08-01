import { useState } from 'react'
import './HospitalConfigScreen.css'

const PRESETS = [7, 30, 90, 180, 365]

export default function HospitalConfigScreen({ onRun, error }) {
  const [days, setDays] = useState(30)
  const [forceMassCasualty, setForceMassCasualty] = useState(false)
  const [touched, setTouched] = useState(false)

  const valid = Number.isInteger(Number(days)) && days >= 1 && days <= 365

  function handleSubmit(e) {
    e.preventDefault()
    if (valid) onRun(Number(days), forceMassCasualty)
  }

  return (
    <div className="hconfig-page">
      <div className="hconfig-card">
        <h1 className="hconfig-title">Hospital Operations Simulator</h1>
        <p className="hconfig-subtitle">
          Simulate patient flow through a 261-bed general hospital. Choose how many days
          to run, then let the engine work through every admission, transfer and discharge.
        </p>

        <form onSubmit={handleSubmit} className="hconfig-form">
          <label className="hconfig-label" htmlFor="hospital-days">
            Number of days to simulate
          </label>
          <input
            id="hospital-days"
            className={`hconfig-input${touched && !valid ? ' hconfig-input--error' : ''}`}
            type="number"
            min={1}
            max={365}
            value={days}
            onChange={e => { setDays(e.target.value); setTouched(true) }}
            onBlur={() => setTouched(true)}
          />
          {touched && !valid
            ? <p className="hconfig-hint hconfig-hint--error">Enter a whole number between 1 and 365.</p>
            : <p className="hconfig-hint">Suggested range: 1 to 365 days</p>
          }

          <div className="hconfig-presets">
            {PRESETS.map(n => (
              <button
                key={n}
                type="button"
                className={`hpreset-btn${Number(days) === n ? ' hpreset-btn--active' : ''}`}
                onClick={() => { setDays(n); setTouched(false) }}
              >
                {n}d
              </button>
            ))}
          </div>

          <label className="hconfig-toggle">
            <input
              type="checkbox"
              checked={forceMassCasualty}
              onChange={e => setForceMassCasualty(e.target.checked)}
            />
            <span className="hconfig-toggle-body">
              <span className="hconfig-toggle-title">Force a mass casualty event</span>
              <span className="hconfig-toggle-note">
                Mass casualties occur at random roughly 3% of days. Enable this to guarantee
                at least one and stress the hospital past its capacity.
              </span>
            </span>
          </label>

          <button className="hrun-btn" type="submit" disabled={!valid}>
            Run Simulation
          </button>
        </form>

        {error && (
          <div className="hconfig-error">
            <strong>Simulation failed:</strong> {error}
          </div>
        )}

        <div className="hconfig-stats">
          <div className="hstat-chip">6 departments</div>
          <div className="hstat-chip">6 patient archetypes</div>
          <div className="hstat-chip">ESI 1-5 triage</div>
          <div className="hstat-chip">4 event types</div>
        </div>
      </div>
    </div>
  )
}
