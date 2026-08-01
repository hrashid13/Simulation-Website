import { useMemo, useState } from 'react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts'
import {
  DEPT_COLORS, DEPT_ORDER, OCCUPANCY_RAMP, GRID_COLOR, TICK_STYLE, fmtPct,
} from './constants'

// Occupancy is a percentage of capacity, so the scale is fixed 0-100 rather
// than fitted to the data. A ward at 84% and a clinic at 18% must not both
// fill their panel.
//
// Heatmap band edges are not evenly spaced. Real occupancy spends almost all of
// its time between 40% and 95%, so even 20-point bands rendered the whole grid
// in two near-identical blues. These are tighter where the data actually lives,
// and the legend states each threshold so the uneven spacing is visible rather
// than hidden.
const OCCUPANCY_BANDS = [0, 30, 50, 65, 80, 92]

function bandColor(pct) {
  let index = 0
  for (let i = 0; i < OCCUPANCY_BANDS.length; i++) {
    if (pct >= OCCUPANCY_BANDS[i]) index = i
  }
  return OCCUPANCY_RAMP[index]
}

function bandLabel(i) {
  const lo = OCCUPANCY_BANDS[i]
  const hi = OCCUPANCY_BANDS[i + 1]
  return hi === undefined ? `${lo}%+` : `${lo}-${hi}%`
}

function PanelTooltip({ active, payload, hourly }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="hchart-tooltip">
      <p className="hct-title">
        Day {d.day}{hourly ? `, ${String(d.hour).padStart(2, '0')}:00` : ''}
      </p>
      <p className="hct-row"><span>Occupancy</span><span>{fmtPct(payload[0].value)}</span></p>
    </div>
  )
}

/**
 * One small panel per department rather than six overlapping lines.
 *
 * The six-department palette carries a colour-vision warning for the amber/green
 * pair, and small multiples remove the problem entirely: each series is isolated
 * by position, so nothing depends on telling two hues apart.
 */
export function OccupancySmallMultiples({ series, departmentStats, resolution }) {
  const hourly = resolution === 'hourly'

  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Bed Occupancy by Department</h4>
      <p className="hchart-sub">
        Share of capacity in use{hourly ? ', sampled hourly' : ', averaged per day'}.
        Each panel is fixed to a 0-100% scale so departments are directly comparable.
      </p>
      <div className="occ-grid">
        {DEPT_ORDER.map(key => {
          const stat = departmentStats[key]
          return (
            <div key={key} className="occ-panel">
              <div className="occ-panel-head">
                <span className="occ-panel-name">
                  <span className="occ-swatch" style={{ background: DEPT_COLORS[key] }} />
                  {stat.name}
                </span>
                <span className="occ-panel-stat mono">{fmtPct(stat.avg_occupancy_pct)}</span>
              </div>
              <ResponsiveContainer width="100%" height={110}>
                <AreaChart data={series} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={DEPT_COLORS[key]} stopOpacity={0.45} />
                      <stop offset="100%" stopColor={DEPT_COLORS[key]} stopOpacity={0.04} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
                  <XAxis dataKey="day" tick={{ ...TICK_STYLE, fontSize: 10 }}
                    minTickGap={24} />
                  <YAxis domain={[0, 100]} ticks={[0, 50, 100]}
                    tick={{ ...TICK_STYLE, fontSize: 10 }} width={30}
                    tickFormatter={v => `${v}%`} />
                  <Tooltip content={<PanelTooltip hourly={hourly} />}
                    cursor={{ stroke: '#8b90a0', strokeWidth: 1 }} />
                  <Area type="monotone" dataKey={key} stroke={DEPT_COLORS[key]}
                    strokeWidth={1.6} fill={`url(#grad-${key})`} isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/**
 * Department x day occupancy grid. Colour is a single-hue sequential ramp, so
 * magnitude is carried by lightness rather than by hue identity.
 */
export function DepartmentOccupancyHeatmap({ series, departmentStats, resolution }) {
  const [hovered, setHovered] = useState(null)

  // An hourly series has 24 rows per day; collapse to a daily mean so the grid
  // stays one column per day at every run length.
  const days = useMemo(() => {
    if (resolution !== 'hourly') return series
    const byDay = new Map()
    for (const row of series) {
      if (!byDay.has(row.day)) byDay.set(row.day, [])
      byDay.get(row.day).push(row)
    }
    return [...byDay.entries()].map(([day, rows]) => {
      const out = { day }
      for (const key of DEPT_ORDER) {
        out[key] = rows.reduce((a, r) => a + r[key], 0) / rows.length
      }
      return out
    })
  }, [series, resolution])

  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Occupancy Heatmap</h4>
      <p className="hchart-sub">
        Daily mean occupancy per department. Brighter means closer to full.
      </p>

      <div className="heatmap-scroll">
        <div className="heatmap" style={{ '--cols': days.length }}>
          {DEPT_ORDER.map(key => (
            <div key={key} className="heatmap-row">
              <span className="heatmap-label">{departmentStats[key].name}</span>
              <div className="heatmap-cells">
                {days.map(d => (
                  <span
                    key={d.day}
                    className="heatmap-cell"
                    style={{ background: bandColor(d[key]) }}
                    onMouseEnter={() => setHovered({ day: d.day, key, value: d[key] })}
                    onMouseLeave={() => setHovered(null)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="heatmap-footer">
        <div className="heatmap-legend">
          {OCCUPANCY_RAMP.map((c, i) => (
            <span key={c} className="heatmap-legend-step">
              <span className="heatmap-legend-swatch" style={{ background: c }} />
              <span className="heatmap-legend-label">{bandLabel(i)}</span>
            </span>
          ))}
        </div>
        <span className="heatmap-readout mono">
          {hovered
            ? `${departmentStats[hovered.key].name} — day ${hovered.day} — ${fmtPct(hovered.value)}`
            : 'Hover a cell for detail'}
        </span>
      </div>
    </div>
  )
}
