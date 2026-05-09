import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { REV_COLORS, DOW_ORDER, fmtMoneyShort, fmtMoney } from './constants'

const PIE_LABELS = ['Ticket Revenue', 'Food & Beverage', 'Retail & Merchandise']

function PieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.05) return null
  const RADIAN = Math.PI / 180
  const r = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + r * Math.cos(-midAngle * RADIAN)
  const y = cy + r * Math.sin(-midAngle * RADIAN)
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={12} fontWeight={600}>
      {(percent * 100).toFixed(1)}%
    </text>
  )
}

function PieTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  return (
    <div className="chart-tooltip">
      <p className="ct-title">{payload[0].name}</p>
      <p className="ct-value">{fmtMoney(payload[0].value)}</p>
      <p className="ct-weather">{(payload[0].payload.percent * 100).toFixed(1)}%</p>
    </div>
  )
}

export function RevenuePieChart({ summary }) {
  const total = summary.total_revenue || 1
  const pieData = [
    { name: PIE_LABELS[0], value: summary.total_ticket_revenue, percent: summary.total_ticket_revenue / total },
    { name: PIE_LABELS[1], value: summary.total_food_beverage_revenue, percent: summary.total_food_beverage_revenue / total },
    { name: PIE_LABELS[2], value: summary.total_retail_merchandise_revenue, percent: summary.total_retail_merchandise_revenue / total },
  ]
  return (
    <div className="chart-block">
      <h4 className="chart-title">Revenue Mix</h4>
      <div className="pie-legend">
        {pieData.map((d, i) => (
          <span key={d.name} className="pie-legend-item">
            <span className="pie-legend-dot" style={{ background: REV_COLORS[i] }} />
            {d.name}
          </span>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={100}
            labelLine={false} label={<PieLabel />} isAnimationActive={false}>
            {pieData.map((_, i) => <Cell key={i} fill={REV_COLORS[i]} />)}
          </Pie>
          <Tooltip content={<PieTooltip />} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RevenueDowChart({ dailyData }) {
  const dowMap = {}
  DOW_ORDER.forEach(d => { dowMap[d] = { total: 0, count: 0 } })
  dailyData.forEach(d => {
    dowMap[d.day_of_week].total += d.total_revenue
    dowMap[d.day_of_week].count++
  })
  const data = DOW_ORDER.map(d => ({
    name: d.slice(0, 3),
    revenue: dowMap[d].count > 0 ? dowMap[d].total / dowMap[d].count : 0,
    weekend: d === 'Saturday' || d === 'Sunday',
  }))
  return (
    <div className="chart-block">
      <h4 className="chart-title">Avg Revenue by Day of Week</h4>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={fmtMoneyShort} tick={{ fontSize: 11 }} width={64} />
          <Tooltip formatter={v => fmtMoney(v)} labelFormatter={l => `${l}`} />
          <Bar dataKey="revenue" name="Avg Revenue" radius={[4, 4, 0, 0]} isAnimationActive={false}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.weekend ? REV_COLORS[2] : REV_COLORS[0]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="chart-note">
        <span style={{ color: REV_COLORS[0] }}>&#9632;</span> Weekday &nbsp;
        <span style={{ color: REV_COLORS[2] }}>&#9632;</span> Weekend
      </div>
    </div>
  )
}
