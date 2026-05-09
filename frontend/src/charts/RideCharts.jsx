import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell,
} from 'recharts'
import { RIDE_COLOR, fmtNum } from './constants'

function buildRideData(rideStats, key) {
  return Object.entries(rideStats)
    .map(([name, s]) => ({ name, value: s[key] }))
    .sort((a, b) => b.value - a.value)
}

const shortName = name => name.length > 14 ? name.slice(0, 13) + '…' : name

export function RideRidersChart({ rideStats }) {
  const data = buildRideData(rideStats, 'total_riders')
  return (
    <div className="chart-block">
      <h4 className="chart-title">Total Riders per Ride</h4>
      <ResponsiveContainer width="100%" height={data.length * 44 + 40}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" horizontal={false} />
          <XAxis type="number" tickFormatter={fmtNum} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" tickFormatter={shortName} tick={{ fontSize: 11 }} width={110} />
          <Tooltip formatter={v => fmtNum(v)} />
          <Bar dataKey="value" name="Total Riders" fill={RIDE_COLOR} radius={[0, 4, 4, 0]} isAnimationActive={false}>
            {data.map((_, i) => <Cell key={i} fill={RIDE_COLOR} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RideUtilizationChart({ rideStats }) {
  const data = Object.entries(rideStats)
    .map(([name, s]) => ({ name, value: +(s.avg_utilization * 100).toFixed(1) }))
    .sort((a, b) => b.value - a.value)
  return (
    <div className="chart-block">
      <h4 className="chart-title">Avg Queue Utilization (%)</h4>
      <ResponsiveContainer width="100%" height={data.length * 44 + 40}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" horizontal={false} />
          <XAxis type="number" tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} domain={[0, 100]} />
          <YAxis type="category" dataKey="name" tickFormatter={shortName} tick={{ fontSize: 11 }} width={110} />
          <Tooltip formatter={v => `${v}%`} />
          <Bar dataKey="value" name="Utilization" radius={[0, 4, 4, 0]} isAnimationActive={false}>
            {data.map((d, i) => <Cell key={i} fill={d.value > 80 ? '#EF5350' : RIDE_COLOR} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
