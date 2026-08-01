import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import {
  REVENUE_COLOR, COST_COLOR, GRID_COLOR, TICK_STYLE, fmtMoney, fmtMoneyShort, fmtNum,
} from './constants'

function FinanceTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="hchart-tooltip">
      <p className="hct-title">{d.name}</p>
      <p className="hct-row"><span>Revenue</span><span>{fmtMoney(d.revenue)}</span></p>
      <p className="hct-row"><span>Cost</span><span>{fmtMoney(d.cost)}</span></p>
      <p className="hct-row">
        <span>Net</span>
        <span className={d.net < 0 ? 'warn' : 'ok'}>{fmtMoney(d.net)}</span>
      </p>
      <p className="hct-row"><span>Encounters</span><span>{fmtNum(d.encounters)}</span></p>
    </div>
  )
}

export function DepartmentFinanceChart({ departmentStats }) {
  const data = Object.values(departmentStats).map(s => ({
    name: s.name,
    revenue: s.revenue,
    cost: s.cost,
    net: s.net_margin,
    encounters: s.total_encounters,
  }))

  return (
    <div className="hchart-block">
      <h4 className="hchart-title">Revenue Against Cost by Department</h4>
      <p className="hchart-sub">
        Flat per-encounter revenue with no payer modelling. Inpatient units running at a loss
        against procedural revenue is the expected shape.
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
          <XAxis type="number" tick={TICK_STYLE} tickFormatter={fmtMoneyShort} />
          <YAxis type="category" dataKey="name" tick={TICK_STYLE} width={116} />
          <Tooltip content={<FinanceTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          <Bar dataKey="revenue" name="Revenue" fill={REVENUE_COLOR}
            radius={[0, 3, 3, 0]} isAnimationActive={false} />
          <Bar dataKey="cost" name="Cost" fill={COST_COLOR}
            radius={[0, 3, 3, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
