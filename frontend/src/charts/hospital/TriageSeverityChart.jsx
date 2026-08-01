import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'
import { ESI_COLORS, GRID_COLOR, TICK_STYLE, fmtNum, fmtDuration, fmtPct } from './constants'

function TriageTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="hchart-tooltip">
      <p className="hct-title">ESI {d.level} — {d.label}</p>
      <p className="hct-row"><span>Patients</span><span>{fmtNum(d.count)}</span></p>
      <p className="hct-row"><span>Share</span><span>{fmtPct(d.share)}</span></p>
      <p className="hct-row"><span>Mean ER wait</span><span>{fmtDuration(d.wait)}</span></p>
      <p className="hct-row"><span>Target</span><span>{d.target}m</span></p>
      <p className="hct-row"><span>Within target</span><span>{d.within}%</span></p>
    </div>
  )
}

export function TriageSeverityChart({ esiStats }) {
  const data = Object.entries(esiStats)
    .map(([level, s]) => ({
      level,
      label: s.label,
      name: `ESI ${level}`,
      count: s.count,
      share: s.share_pct,
      wait: s.avg_er_wait_minutes,
      target: s.target_wait_minutes,
      within: s.within_target_pct,
    }))
    .sort((a, b) => Number(a.level) - Number(b.level))

  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Triage Severity Mix</h4>
      <p className="hchart-sub">
        Emergency Severity Index, 1 is most severe. Includes clinic and elective arrivals,
        which sit at ESI 4-5.
      </p>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
          <XAxis type="number" tick={TICK_STYLE} tickFormatter={fmtNum} />
          <YAxis type="category" dataKey="name" tick={TICK_STYLE} width={56} />
          <Tooltip content={<TriageTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="count" radius={[0, 3, 3, 0]} isAnimationActive={false}
            label={{ position: 'right', fill: '#8b90a0', fontSize: 11,
                     formatter: v => `${v.toLocaleString()}` }}>
            {data.map(d => <Cell key={d.level} fill={ESI_COLORS[d.level]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Share of each triage band seen inside its benchmark time-to-provider. This is
 * the metric an actual emergency department dashboard leads with.
 */
export function TriageTargetTable({ esiStats }) {
  const rows = Object.entries(esiStats).sort((a, b) => Number(a[0]) - Number(b[0]))

  return (
    <div className="htable-block">
      <h4 className="hchart-title">Time to Provider Against ESI Targets</h4>
      <div className="htable-scroll">
        <table className="hdata-table">
          <thead>
            <tr>
              <th>ESI</th><th>Severity</th><th>Patients</th><th>Share</th>
              <th>Mean ER Wait</th><th>Target</th><th>Within Target</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([level, s]) => (
              <tr key={level}>
                <td>
                  <span className="esi-chip" style={{ background: ESI_COLORS[level] }}>{level}</span>
                </td>
                <td>{s.label}</td>
                <td className="mono">{fmtNum(s.count)}</td>
                <td className="mono">{fmtPct(s.share_pct)}</td>
                <td className="mono">{fmtDuration(s.avg_er_wait_minutes)}</td>
                <td className="mono">{s.target_wait_minutes}m</td>
                <td className="mono">
                  <span className={s.within_target_pct >= 80 ? 'ok' : 'warn'}>
                    {fmtPct(s.within_target_pct)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
