import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { ARCH_COLORS, GRID_COLOR, TICK_STYLE, fmtMoney, fmtMoneyShort } from './constants'

function ArchTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0]
  return (
    <div className="chart-tooltip">
      <p className="ct-title">{d.name}</p>
      <p className="ct-value">{d.value.toLocaleString()} visitors</p>
      <p className="ct-weather">{(d.payload.percent * 100).toFixed(1)}%</p>
    </div>
  )
}

function PieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.04) return null
  const RADIAN = Math.PI / 180
  const r = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + r * Math.cos(-midAngle * RADIAN)
  const y = cy + r * Math.sin(-midAngle * RADIAN)
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={600}>
      {(percent * 100).toFixed(0)}%
    </text>
  )
}

export function ArchetypePieChart({ archTotals }) {
  const totalVisitors = Object.values(archTotals).reduce((a, b) => a + b, 0) || 1
  const data = Object.entries(archTotals)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value, percent: value / totalVisitors }))
    .sort((a, b) => b.value - a.value)

  return (
    <div className="chart-block">
      <h4 className="chart-title">Visitor Archetype Distribution</h4>
      <div className="pie-legend">
        {data.map((d, i) => (
          <span key={d.name} className="pie-legend-item">
            <span className="pie-legend-dot" style={{ background: ARCH_COLORS[i % ARCH_COLORS.length] }} />
            {d.name}
          </span>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={data} dataKey="value" cx="50%" cy="50%" outerRadius={100}
            labelLine={false} label={<PieLabel />} isAnimationActive={false}>
            {data.map((_, i) => <Cell key={i} fill={ARCH_COLORS[i % ARCH_COLORS.length]} />)}
          </Pie>
          <Tooltip content={<ArchTooltip />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AvgSpendChart({ dailyData }) {
  const xInterval = dailyData.length <= 30 ? 4 : dailyData.length <= 90 ? 13 : 29
  return (
    <div className="chart-block">
      <h4 className="chart-title">Avg Spend per Visitor per Day</h4>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={dailyData} margin={{ top: 8, right: 16, bottom: 0, left: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
          <XAxis dataKey="day" tick={TICK_STYLE} interval={xInterval}
            label={{ value: 'Day', position: 'insideBottomRight', offset: -4, fontSize: 11, fill: '#8b90a0' }} />
          <YAxis tickFormatter={fmtMoneyShort} tick={TICK_STYLE} width={64} />
          <Tooltip formatter={v => fmtMoney(v)} labelFormatter={l => `Day ${l}`} />
          <Line type="monotone" dataKey="avg_spend_per_visitor" name="Avg Spend"
            stroke="#a78bfa" strokeWidth={1.8} dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
