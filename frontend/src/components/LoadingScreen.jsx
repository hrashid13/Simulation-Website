import './LoadingScreen.css'

const STEPS = [
  'Rolling weather conditions...',
  'Generating visitor groups...',
  'Simulating ride queues...',
  'Tallying store revenue...',
  'Calculating ticket sales...',
  'Logging incidents...',
  'Building your report...',
]

export default function LoadingScreen({ days, steps = STEPS }) {
  return (
    <div className="loading-page">
      <div className="loading-card">
        <div className="spinner" />
        <h2 className="loading-title">Simulating {days} days...</h2>
        <p className="loading-sub">This usually takes under 10 seconds.</p>
        <ul className="loading-steps">
          {steps.map(step => (
            <li key={step} className="loading-step">{step}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
