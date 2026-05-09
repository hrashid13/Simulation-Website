export default function ReportScreen({ data, days, onReset }) {
  return (
    <div style={{ padding: 40 }}>
      <h1>Report — {days}-day simulation (coming in step 6)</h1>
      <button onClick={onReset}>Run another simulation</button>
    </div>
  )
}
