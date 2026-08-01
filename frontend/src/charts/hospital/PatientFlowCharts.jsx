import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Cell,
} from 'recharts'
import {
  FLOW_COLORS, DIVERSION_COLOR, EVENT_COLORS, GRID_COLOR, TICK_STYLE,
  fmtNum, dayInterval,
} from './constants'

function FlowTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="hchart-tooltip">
      <p className="hct-title">Day {d.day} — {d.day_of_week}</p>
      <p className="hct-event" style={{ color: EVENT_COLORS[d.event] }}>{d.event}</p>
      <p className="hct-row"><span>Arrivals</span><span>{fmtNum(d.arrivals)}</span></p>
      <p className="hct-row"><span>Discharges</span><span>{fmtNum(d.discharges)}</span></p>
      <p className="hct-row"><span>Admissions</span><span>{fmtNum(d.admissions)}</span></p>
    </div>
  )
}

export function PatientFlowChart({ dailyData }) {
  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Daily Patient Throughput</h4>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={dailyData} margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
          <XAxis dataKey="day" tick={TICK_STYLE} interval={dayInterval(dailyData.length)} />
          <YAxis tick={TICK_STYLE} width={48} tickFormatter={fmtNum} />
          <Tooltip content={<FlowTooltip />} cursor={{ stroke: '#8b90a0', strokeWidth: 1 }} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          <Line type="monotone" dataKey="arrivals" name="Arrivals"
            stroke={FLOW_COLORS.arrivals} strokeWidth={2} dot={false} isAnimationActive={false} />
          <Line type="monotone" dataKey="discharges" name="Discharges"
            stroke={FLOW_COLORS.discharges} strokeWidth={2} dot={false} isAnimationActive={false} />
          <Line type="monotone" dataKey="admissions" name="Inpatient admissions"
            stroke={FLOW_COLORS.admissions} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function DiversionTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="hchart-tooltip">
      <p className="hct-title">Day {d.day} — {d.day_of_week}</p>
      <p className="hct-event" style={{ color: EVENT_COLORS[d.event] }}>{d.event}</p>
      <p className="hct-row"><span>Diverted</span><span>{fmtNum(d.diversions)}</span></p>
      <p className="hct-row"><span>Arrivals</span><span>{fmtNum(d.arrivals)}</span></p>
    </div>
  )
}

export function DiversionChart({ dailyData }) {
  const anyDiversions = dailyData.some(d => d.diversions > 0)

  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Diversions</h4>
      <p className="hchart-sub">
        Lower-acuity arrivals turned away while a unit was full. Critical cases are never diverted.
      </p>
      {anyDiversions ? (
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={dailyData} margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
            <XAxis dataKey="day" tick={TICK_STYLE} interval={dayInterval(dailyData.length)} />
            <YAxis tick={TICK_STYLE} width={40} allowDecimals={false} />
            <Tooltip content={<DiversionTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
            <Bar dataKey="diversions" fill={DIVERSION_COLOR} radius={[3, 3, 0, 0]}
              isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <p className="hchart-empty">
          No patients were diverted. The hospital absorbed every arrival across this run.
        </p>
      )}
    </div>
  )
}

function EventTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="hchart-tooltip">
      <p className="hct-title">{d.event}</p>
      <p className="hct-row"><span>Days</span><span>{d.count}</span></p>
      <p className="hct-row"><span>Mean arrivals</span><span>{d.avg_arrivals.toFixed(1)}</span></p>
      <p className="hct-row"><span>Mean diversions</span><span>{d.avg_diversions.toFixed(2)}</span></p>
    </div>
  )
}

export function EventImpactChart({ eventSummary }) {
  const data = Object.entries(eventSummary)
    .map(([event, b]) => ({ event, ...b }))
    .sort((a, b) => b.avg_arrivals - a.avg_arrivals)

  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Mean Daily Arrivals by Event</h4>
      <ResponsiveContainer width="100%" height={230}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 44, bottom: 4, left: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
          <XAxis type="number" tick={TICK_STYLE} />
          <YAxis type="category" dataKey="event" tick={TICK_STYLE} width={122} />
          <Tooltip content={<EventTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="avg_arrivals" radius={[0, 3, 3, 0]} isAnimationActive={false}
            label={{ position: 'right', fill: '#8b90a0', fontSize: 11,
                     formatter: v => v.toFixed(0) }}>
            {data.map(d => (
              <Cell key={d.event} fill={EVENT_COLORS[d.event] || '#8b90a0'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
