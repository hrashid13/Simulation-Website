import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'
import {
  DEPT_COLORS, GRID_COLOR, TICK_STYLE, fmtDuration,
} from './constants'

function WaitTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="hchart-tooltip">
      <p className="hct-title">{d.name}</p>
      <p className="hct-row"><span>Mean wait</span><span>{fmtDuration(d.avg)}</span></p>
      <p className="hct-row"><span>Longest wait</span><span>{fmtDuration(d.max)}</span></p>
      <p className="hct-row"><span>Encounters</span><span>{d.encounters.toLocaleString()}</span></p>
    </div>
  )
}

export function WaitTimeChart({ departmentStats }) {
  const data = Object.entries(departmentStats)
    .filter(([, s]) => s.queue_reported)
    .map(([key, s]) => ({
      key,
      name: s.name,
      avg: s.avg_wait_minutes,
      max: s.max_wait_minutes,
      encounters: s.total_encounters,
    }))

  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Mean Wait for a Bed</h4>
      <p className="hchart-sub">
        Outside the emergency department this is boarding time — the delay moving a patient
        who is already admitted into the right unit.
      </p>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 52, bottom: 4, left: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
          <XAxis type="number" tick={TICK_STYLE} tickFormatter={fmtDuration} />
          <YAxis type="category" dataKey="name" tick={TICK_STYLE} width={116} />
          <Tooltip content={<WaitTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          {/* Direct labels: the amber and green fills sit in the CVD floor band,
              so the value must never depend on reading the colour. */}
          <Bar dataKey="avg" radius={[0, 3, 3, 0]} isAnimationActive={false}
            label={{ position: 'right', fill: '#8b90a0', fontSize: 11, formatter: fmtDuration }}>
            {data.map(d => <Cell key={d.key} fill={DEPT_COLORS[d.key]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
