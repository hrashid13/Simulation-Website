import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from 'recharts'
import { W_COLORS, GRID_COLOR, TICK_STYLE, fmtNum, fmtMoneyShort } from './constants'

function WeatherDot({ cx, cy, payload }) {
  const color = W_COLORS[payload.weather] || '#64748b'
  return <circle cx={cx} cy={cy} r={3} fill={color} strokeWidth={0} />
}

function WeatherLegend() {
  return (
    <div className="weather-legend">
      {Object.entries(W_COLORS).map(([w, c]) => (
        <span key={w} className="weather-legend-item">
          <span className="weather-legend-dot" style={{ background: c }} />
          {w}
        </span>
      ))}
    </div>
  )
}

function AttendanceTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="chart-tooltip">
      <p className="ct-title">Day {d.day} — {d.day_of_week}</p>
      <p className="ct-weather">{d.weather}</p>
      <p className="ct-value">{fmtNum(d.attendance)} visitors</p>
    </div>
  )
}

function RevenueTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="chart-tooltip">
      <p className="ct-title">Day {d.day} — {d.day_of_week}</p>
      <p className="ct-weather">{d.weather}</p>
      <p className="ct-value">{fmtMoneyShort(d.total_revenue)}</p>
    </div>
  )
}

const xInterval = data =>
  data.length <= 30 ? 4 : data.length <= 90 ? 13 : data.length <= 180 ? 29 : 59

export function AttendanceChart({ dailyData }) {
  return (
    <div className="chart-block">
      <h4 className="chart-title">Daily Attendance</h4>
      <WeatherLegend />
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={dailyData} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
          <XAxis dataKey="day" tick={TICK_STYLE} interval={xInterval(dailyData)}
            label={{ value: 'Day', position: 'insideBottomRight', offset: -4, fontSize: 11, fill: '#8b90a0' }} />
          <YAxis tickFormatter={fmtNum} tick={TICK_STYLE} width={60} />
          <Tooltip content={<AttendanceTooltip />} />
          <Line
            type="monotone" dataKey="attendance" stroke="#8b90a0" strokeWidth={1.5}
            dot={<WeatherDot />} activeDot={{ r: 5 }} isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RevenueTrendChart({ dailyData }) {
  return (
    <div className="chart-block">
      <h4 className="chart-title">Daily Total Revenue</h4>
      <WeatherLegend />
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={dailyData} margin={{ top: 8, right: 16, bottom: 0, left: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
          <XAxis dataKey="day" tick={TICK_STYLE} interval={xInterval(dailyData)}
            label={{ value: 'Day', position: 'insideBottomRight', offset: -4, fontSize: 11, fill: '#8b90a0' }} />
          <YAxis tickFormatter={fmtMoneyShort} tick={TICK_STYLE} width={64} />
          <Tooltip content={<RevenueTooltip />} />
          <Line
            type="monotone" dataKey="total_revenue" stroke="#4f8ef7" strokeWidth={1.5}
            dot={<WeatherDot />} activeDot={{ r: 5 }} isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
