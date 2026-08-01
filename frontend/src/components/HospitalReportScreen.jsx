import { useState } from 'react'
import {
  PatientFlowChart, DiversionChart, EventImpactChart,
} from '../charts/hospital/PatientFlowCharts'
import {
  OccupancySmallMultiples, DepartmentOccupancyHeatmap,
} from '../charts/hospital/OccupancyCharts'
import { WaitTimeChart } from '../charts/hospital/WaitTimeChart'
import { TriageSeverityChart, TriageTargetTable } from '../charts/hospital/TriageSeverityChart'
import { DepartmentFinanceChart } from '../charts/hospital/FinancialCharts'
import {
  EVENT_COLORS, fmtNum, fmtMoney, fmtPct, fmtDuration,
} from '../charts/hospital/constants'
import './HospitalReportScreen.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const SECTIONS = [
  { id: 'h-summary', label: 'Summary' },
  { id: 'h-flow', label: 'Patient Flow' },
  { id: 'h-occupancy', label: 'Occupancy' },
  { id: 'h-triage', label: 'Wait & Triage' },
  { id: 'h-strain', label: 'Capacity Strain' },
  { id: 'h-finance', label: 'Financials' },
  { id: 'h-events', label: 'Events' },
]

function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function HospitalReportScreen({ data, days, onReset, onHome }) {
  const [downloading, setDownloading] = useState(null)
  const [exportError, setExportError] = useState(null)

  async function triggerDownload(endpoint, filename, kind) {
    setDownloading(kind)
    setExportError(null)
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setExportError('Export failed. Please try again.')
    } finally {
      setDownloading(null)
    }
  }

  const downloadPDF = () =>
    triggerDownload('/report/hospital/pdf', `hospitalsim_report_${days}days.pdf`, 'pdf')
  const downloadCSV = () =>
    triggerDownload('/export/hospital/csv', `hospitalsim_data_${days}days.zip`, 'csv')
  const downloadSQL = () =>
    triggerDownload('/export/hospital/sql', `hospitalsim_data_${days}days.sql`, 'sql')

  const busy = downloading !== null

  const {
    summary, daily_data, department_stats, service_stats, esi_stats,
    occupancy_series, disruptions,
  } = data

  return (
    <div className="hreport-page">
      <header className="hreport-header">
        <div className="hreport-header-inner">
          <div className="hreport-header-title">
            <span>{days}-Day Hospital Report</span>
          </div>
          <nav className="hreport-nav">
            {SECTIONS.map(s => (
              <button key={s.id} className="hnav-btn" onClick={() => scrollTo(s.id)}>
                {s.label}
              </button>
            ))}
          </nav>
          <div className="hreport-header-actions">
            {onHome && (
              <button className="haction-btn haction-btn--home" onClick={onHome}>
                Home
              </button>
            )}
            <div className="hexport-group">
              <button className="haction-btn haction-btn--pdf" onClick={downloadPDF}
                disabled={busy}>
                {downloading === 'pdf' ? 'Generating...' : 'PDF'}
              </button>
              <button className="haction-btn haction-btn--csv" onClick={downloadCSV}
                disabled={busy}>
                {downloading === 'csv' ? 'Building...' : 'CSV'}
              </button>
              <button className="haction-btn haction-btn--sql" onClick={downloadSQL}
                disabled={busy}>
                {downloading === 'sql' ? 'Building...' : 'SQL'}
              </button>
            </div>
            {exportError && <span className="hexport-error">{exportError}</span>}
            <button className="haction-btn haction-btn--reset" onClick={onReset}
              disabled={busy}>
              New Simulation
            </button>
          </div>
        </div>
      </header>

      <main className="hreport-main">

        <section id="h-summary" className="hreport-section">
          <h2 className="hsection-title">1. Executive Summary</h2>
          <div className="hkpi-grid">
            <Kpi label="Simulation Period" value={`${summary.total_days} days`} />
            <Kpi label="Patients" value={fmtNum(summary.total_patients)} />
            <Kpi label="Mean ER Wait" value={fmtDuration(summary.avg_er_wait_minutes)} highlight />
            <Kpi label="Inpatient Admissions" value={fmtNum(summary.total_admissions)} />
            <Kpi label="Readmission Rate" value={fmtPct(summary.readmission_rate_pct)} />
            <Kpi label="Diverted" value={fmtNum(summary.total_diversions)} />
            <Kpi label="Satisfaction" value={`${summary.avg_satisfaction}/100`} />
            <Kpi label="Operating Margin" value={fmtPct(summary.net_margin_pct)} />
          </div>
          <div className="hday-row">
            <DayCard
              label="Busiest Day" color="#3987e5" day={summary.busiest_day}
              stat={`${fmtNum(summary.busiest_day.arrivals)} arrivals`}
            />
            <DayCard
              label="Worst Day" color="#e66767" day={summary.worst_day}
              stat={`${fmtDuration(summary.worst_day.avg_er_wait_minutes)} mean ER wait`}
              sub={`${fmtNum(summary.worst_day.diversions)} diverted`}
            />
          </div>
          <p className="hsection-note">
            Worst day is ranked by mean emergency department wait, then by diversions.
            Readmission rate is measured at discharge, so it does not shrink on short runs.
          </p>
        </section>

        <section id="h-flow" className="hreport-section">
          <h2 className="hsection-title">2. Patient Flow and Throughput</h2>
          <PatientFlowChart dailyData={daily_data} />
          <ThroughputTable dailyData={daily_data} summary={summary} />
        </section>

        <section id="h-occupancy" className="hreport-section">
          <h2 className="hsection-title">3. Department Occupancy</h2>
          <OccupancySmallMultiples
            series={occupancy_series}
            departmentStats={department_stats}
            resolution={summary.occupancy_resolution}
          />
          <DepartmentOccupancyHeatmap
            series={occupancy_series}
            departmentStats={department_stats}
            resolution={summary.occupancy_resolution}
          />
          <DepartmentTable departmentStats={department_stats} />
        </section>

        <section id="h-triage" className="hreport-section">
          <h2 className="hsection-title">4. Wait Times and Triage</h2>
          <div className="hchart-grid-2">
            <WaitTimeChart departmentStats={department_stats} />
            <TriageSeverityChart esiStats={esi_stats} />
          </div>
          <TriageTargetTable esiStats={esi_stats} />
        </section>

        <section id="h-strain" className="hreport-section">
          <h2 className="hsection-title">5. Capacity Strain</h2>
          <DiversionChart dailyData={daily_data} />
          <StaffingTable departmentStats={department_stats} />
          <DisruptionTable disruptions={disruptions} />
        </section>

        <section id="h-finance" className="hreport-section">
          <h2 className="hsection-title">6. Financial Performance</h2>
          <DepartmentFinanceChart departmentStats={department_stats} />
          <FinanceTable
            departmentStats={department_stats}
            serviceStats={service_stats}
            summary={summary}
          />
        </section>

        <section id="h-events" className="hreport-section">
          <h2 className="hsection-title">7. Event Impact</h2>
          <EventImpactChart eventSummary={summary.event_summary} />
          <EventTable eventSummary={summary.event_summary} />
        </section>

      </main>
    </div>
  )
}

function Kpi({ label, value, highlight }) {
  return (
    <div className={`hkpi-card${highlight ? ' hkpi-card--highlight' : ''}`}>
      <span className="hkpi-label">{label}</span>
      <span className="hkpi-value mono">{value}</span>
    </div>
  )
}

function DayCard({ label, day, color, stat, sub }) {
  return (
    <div className="hday-card" style={{ borderTopColor: color }}>
      <p className="hday-label">{label}</p>
      <p className="hday-main">Day {day.day} — {day.day_of_week}</p>
      <p className="hday-meta">
        <span className="hevent-badge" style={{ background: EVENT_COLORS[day.event] }}>
          {day.event}
        </span>
      </p>
      <p className="hday-stat mono">{stat}</p>
      {sub && <p className="hday-sub">{sub}</p>}
    </div>
  )
}

function ThroughputTable({ dailyData, summary }) {
  const n = dailyData.length || 1
  const sum = k => dailyData.reduce((a, d) => a + d[k], 0)
  const rows = [
    ['Arrivals', summary.total_patients, summary.total_patients / n],
    ['Inpatient admissions', summary.total_admissions, summary.total_admissions / n],
    ['Discharges', summary.total_discharges, summary.total_discharges / n],
    ['Transfers between units', summary.total_transfers, summary.total_transfers / n],
    ['Diverted', summary.total_diversions, summary.total_diversions / n],
    ['Complications', summary.total_complications, sum('complications') / n],
  ]
  return (
    <div className="htable-block">
      <h4 className="hchart-title">Throughput</h4>
      <div className="htable-scroll">
        <table className="hdata-table">
          <thead><tr><th>Measure</th><th>Total</th><th>Daily mean</th></tr></thead>
          <tbody>
            {rows.map(([label, total, mean]) => (
              <tr key={label}>
                <td>{label}</td>
                <td className="mono">{fmtNum(total)}</td>
                <td className="mono">{mean.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function DepartmentTable({ departmentStats }) {
  return (
    <div className="htable-block">
      <h4 className="hchart-title">Department Detail</h4>
      <div className="htable-scroll">
        <table className="hdata-table">
          <thead>
            <tr>
              <th>Department</th><th>Capacity</th><th>Mean Occ.</th><th>Peak Occ.</th>
              <th>Encounters</th><th>Bed Hours</th>
            </tr>
          </thead>
          <tbody>
            {Object.values(departmentStats).map(s => (
              <tr key={s.name}>
                <td>{s.name}</td>
                <td className="mono">{s.capacity} {s.unit}</td>
                <td className="mono">{fmtPct(s.avg_occupancy_pct)}</td>
                <td className="mono">{fmtPct(s.peak_occupancy_pct)}</td>
                <td className="mono">{fmtNum(s.total_encounters)}</td>
                <td className="mono">{fmtNum(Math.round(s.total_bed_hours))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StaffingTable({ departmentStats }) {
  return (
    <div className="htable-block">
      <h4 className="hchart-title">Staffing and Disruption</h4>
      <div className="htable-scroll">
        <table className="hdata-table">
          <thead>
            <tr>
              <th>Department</th><th>Staffed Level</th><th>Staff Utilisation</th>
              <th>Disruptions</th><th>Hours Lost</th>
            </tr>
          </thead>
          <tbody>
            {Object.values(departmentStats).map(s => (
              <tr key={s.name}>
                <td>{s.name}</td>
                <td className="mono">{s.staffed_level}</td>
                <td className="mono">
                  <span className={s.staff_utilization_pct > 100 ? 'warn' : ''}>
                    {fmtPct(s.staff_utilization_pct)}
                  </span>
                </td>
                <td className="mono">{s.disruption_count}</td>
                <td className="mono">{s.disruption_hours}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="hsection-note">
        Staff utilisation weights each patient by the staffing intensity of their archetype,
        so it can exceed 100%. The rostered level is fixed against bed capacity while demand
        rises with case acuity — above 100% means understaffed for the mix received,
        not that staff were double-booked.
      </p>
    </div>
  )
}

function DisruptionTable({ disruptions }) {
  if (!disruptions.length) {
    return (
      <div className="htable-block">
        <h4 className="hchart-title">Disruption Log</h4>
        <p className="hchart-empty">No disruptions were recorded during this simulation.</p>
      </div>
    )
  }
  return (
    <div className="htable-block">
      <h4 className="hchart-title">Disruption Log ({disruptions.length})</h4>
      <div className="htable-scroll htable-scroll--tall">
        <table className="hdata-table">
          <thead><tr><th>Day</th><th>Department</th><th>Disruption</th><th>Hours</th></tr></thead>
          <tbody>
            {disruptions.map((d, i) => (
              <tr key={`${d.day}-${d.department}-${i}`}>
                <td className="mono">{d.day}</td>
                <td>{d.department}</td>
                <td>{d.type}</td>
                <td className="mono">{d.hours}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function FinanceTable({ departmentStats, serviceStats, summary }) {
  return (
    <div className="htable-block">
      <h4 className="hchart-title">Revenue and Cost Detail</h4>
      <div className="htable-scroll">
        <table className="hdata-table">
          <thead>
            <tr><th>Line</th><th>Encounters</th><th>Revenue</th><th>Cost</th><th>Net</th></tr>
          </thead>
          <tbody>
            {Object.values(departmentStats).map(s => (
              <tr key={s.name}>
                <td>{s.name}</td>
                <td className="mono">{fmtNum(s.total_encounters)}</td>
                <td className="mono">{fmtMoney(s.revenue)}</td>
                <td className="mono">{fmtMoney(s.cost)}</td>
                <td className="mono">
                  <span className={s.net_margin < 0 ? 'warn' : 'ok'}>{fmtMoney(s.net_margin)}</span>
                </td>
              </tr>
            ))}
            {Object.values(serviceStats).map(s => (
              <tr key={s.name}>
                <td>{s.name} <span className="hmuted">(service)</span></td>
                <td className="mono">{fmtNum(s.total_transactions)}</td>
                <td className="mono">{fmtMoney(s.revenue)}</td>
                <td className="mono">—</td>
                <td className="mono"><span className="ok">{fmtMoney(s.revenue)}</span></td>
              </tr>
            ))}
            <tr className="htable-total">
              <td>Total</td>
              <td className="mono">—</td>
              <td className="mono">{fmtMoney(summary.total_revenue)}</td>
              <td className="mono">{fmtMoney(summary.total_cost)}</td>
              <td className="mono">
                <span className={summary.net_margin < 0 ? 'warn' : 'ok'}>
                  {fmtMoney(summary.net_margin)}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

function EventTable({ eventSummary }) {
  return (
    <div className="htable-block">
      <h4 className="hchart-title">Event Detail</h4>
      <div className="htable-scroll">
        <table className="hdata-table">
          <thead>
            <tr><th>Event</th><th>Days</th><th>Mean Arrivals</th><th>Mean Diversions</th>
              <th>Total Arrivals</th></tr>
          </thead>
          <tbody>
            {Object.entries(eventSummary).map(([name, b]) => (
              <tr key={name}>
                <td>
                  <span className="hevent-badge" style={{ background: EVENT_COLORS[name] }}>
                    {name}
                  </span>
                </td>
                <td className="mono">{b.count}</td>
                <td className="mono">{b.avg_arrivals.toFixed(1)}</td>
                <td className="mono">{b.avg_diversions.toFixed(2)}</td>
                <td className="mono">{fmtNum(b.total_arrivals)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
