import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell, Legend,
} from 'recharts'
import { FB_COLOR, RETAIL_COLOR, DOW_ORDER, GRID_COLOR, TICK_STYLE, fmtMoneyShort, fmtMoney } from './constants'

const shortName = name => name.length > 16 ? name.slice(0, 15) + '…' : name

export function StoreRevenueChart({ storeStats }) {
  const data = Object.entries(storeStats)
    .map(([name, s]) => ({ name, value: s.total_revenue, cat: s.category }))
    .sort((a, b) => b.value - a.value)
  return (
    <div className="chart-block">
      <h4 className="chart-title">Total Revenue by Store (ranked)</h4>
      <div className="chart-note" style={{ marginBottom: 8 }}>
        <span style={{ color: FB_COLOR }}>&#9632;</span> Food &amp; Beverage &nbsp;
        <span style={{ color: RETAIL_COLOR }}>&#9632;</span> Retail &amp; Merchandise
      </div>
      <ResponsiveContainer width="100%" height={data.length * 40 + 40}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 60, bottom: 4, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
          <XAxis type="number" tickFormatter={fmtMoneyShort} tick={TICK_STYLE} />
          <YAxis type="category" dataKey="name" tickFormatter={shortName} tick={TICK_STYLE} width={120} />
          <Tooltip formatter={v => fmtMoney(v)} />
          <Bar dataKey="value" name="Revenue" radius={[0, 4, 4, 0]} isAnimationActive={false}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.cat === 'food_beverage' ? FB_COLOR : RETAIL_COLOR} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function StoreDailyChart({ dailyData }) {
  const useDow = dailyData.length > 60
  let chartData

  if (useDow) {
    const map = {}
    DOW_ORDER.forEach(d => { map[d] = { fb: 0, retail: 0, count: 0 } })
    dailyData.forEach(d => {
      map[d.day_of_week].fb += d.food_beverage_revenue
      map[d.day_of_week].retail += d.retail_merchandise_revenue
      map[d.day_of_week].count++
    })
    chartData = DOW_ORDER.map(d => ({
      name: d.slice(0, 3),
      fb: map[d].count ? map[d].fb / map[d].count : 0,
      retail: map[d].count ? map[d].retail / map[d].count : 0,
    }))
  } else {
    chartData = dailyData.map(d => ({
      name: `D${d.day}`,
      fb: d.food_beverage_revenue,
      retail: d.retail_merchandise_revenue,
    }))
  }

  const title = useDow
    ? 'Avg Food & Bev vs Retail by Day of Week'
    : 'Food & Bev vs Retail Revenue per Day'

  return (
    <div className="chart-block">
      <h4 className="chart-title">{title}</h4>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 8, right: 16, bottom: 0, left: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
          <XAxis dataKey="name" tick={TICK_STYLE} interval={useDow ? 0 : 'preserveStartEnd'} />
          <YAxis tickFormatter={fmtMoneyShort} tick={TICK_STYLE} width={64} />
          <Tooltip formatter={v => fmtMoney(v)} />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11, color: '#8b90a0' }} />
          <Bar dataKey="fb" name="Food & Bev" fill={FB_COLOR} isAnimationActive={false} />
          <Bar dataKey="retail" name="Retail" fill={RETAIL_COLOR} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
