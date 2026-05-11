import { useState } from 'react'
import { AttendanceChart, RevenueTrendChart } from '../charts/DailyTrendsCharts'
import { RevenuePieChart, RevenueDowChart } from '../charts/RevenueCharts'
import { RideRidersChart, RideUtilizationChart } from '../charts/RideCharts'
import { StoreRevenueChart, StoreDailyChart } from '../charts/StoreCharts'
import { ArchetypePieChart, AvgSpendChart } from '../charts/DemographicsCharts'
import { fmtMoney, fmtNum, W_COLORS } from '../charts/constants'
import './ReportScreen.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const SECTIONS = [
  { id: 'summary', label: 'Summary' },
  { id: 'trends', label: 'Daily Trends' },
  { id: 'revenue', label: 'Revenue' },
  { id: 'rides', label: 'Rides' },
  { id: 'stores', label: 'Stores' },
  { id: 'demographics', label: 'Demographics' },
  { id: 'weather', label: 'Weather' },
  { id: 'incidents', label: 'Incidents' },
]

function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function ReportScreen({ data, days, onReset }) {
  const [activeDownload, setActiveDownload] = useState(null) // 'pdf' | 'csv' | 'sql' | null
  const [exportError, setExportError] = useState(null)

  async function triggerDownload(endpoint, filename, type) {
    setActiveDownload(type)
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
      setActiveDownload(null)
    }
  }

  const busy = activeDownload !== null

  function downloadPDF() {
    triggerDownload('/report/pdf', `parksim_report_${days}days.pdf`, 'pdf')
  }
  function downloadCSV() {
    triggerDownload('/export/csv', `parksim_data_${days}days.zip`, 'csv')
  }
  function downloadSQL() {
    triggerDownload('/export/sql', `parksim_data_${days}days.sql`, 'sql')
  }

  const { summary, daily_data, ride_stats, store_stats, ticket_stats, incidents } = data

  return (
    <div className="report-page">
      <header className="report-header">
        <div className="report-header-inner">
          <div className="report-header-title">
            <span className="report-header-icon">🎡</span>
            <span>{days}-Day Simulation Report</span>
          </div>
          <nav className="report-nav">
            {SECTIONS.map(s => (
              <button key={s.id} className="nav-btn" onClick={() => scrollTo(s.id)}>
                {s.label}
              </button>
            ))}
          </nav>
          <div className="report-header-actions">
            <div className="export-btn-group">
              <button className="action-btn action-btn--pdf" onClick={downloadPDF} disabled={busy}>
                {activeDownload === 'pdf' ? 'Generating…' : 'PDF'}
              </button>
              <button className="action-btn action-btn--csv" onClick={downloadCSV} disabled={busy}>
                {activeDownload === 'csv' ? 'Building…' : 'CSV'}
              </button>
              <button className="action-btn action-btn--sql" onClick={downloadSQL} disabled={busy}>
                {activeDownload === 'sql' ? 'Building…' : 'SQL'}
              </button>
            </div>
            {exportError && <span className="export-error">{exportError}</span>}
            <button className="action-btn action-btn--reset" onClick={onReset} disabled={busy}>
              New Simulation
            </button>
          </div>
        </div>
      </header>

      <main className="report-main">

        {/* Section 1 */}
        <section id="summary" className="report-section">
          <h2 className="section-title">1. Executive Summary</h2>
          <div className="kpi-grid">
            <KpiCard label="Simulation Period" value={`${summary.total_days} days`} />
            <KpiCard label="Total Attendance" value={fmtNum(summary.total_attendance)} />
            <KpiCard label="Total Revenue" value={fmtMoney(summary.total_revenue)} highlight />
            <KpiCard label="Most Popular Ride" value={summary.most_popular_ride} />
            <KpiCard label="Top Grossing Store" value={summary.top_grossing_store} />
          </div>
          <div className="day-highlight-row">
            <DayCard label="Best Day" day={summary.best_day} color="#2E7D32" />
            <DayCard label="Worst Day" day={summary.worst_day} color="#C62828" />
          </div>
        </section>

        {/* Section 2 */}
        <section id="trends" className="report-section">
          <h2 className="section-title">2. Daily Attendance & Revenue Trends</h2>
          <div className="chart-grid-1">
            <AttendanceChart dailyData={daily_data} />
            <RevenueTrendChart dailyData={daily_data} />
          </div>
        </section>

        {/* Section 3 */}
        <section id="revenue" className="report-section">
          <h2 className="section-title">3. Revenue Breakdown</h2>
          <div className="chart-grid-2">
            <RevenuePieChart summary={summary} />
            <RevenueDowChart dailyData={daily_data} />
          </div>
        </section>

        {/* Section 4 */}
        <section id="rides" className="report-section">
          <h2 className="section-title">4. Ride Analytics</h2>
          <div className="chart-grid-2">
            <RideRidersChart rideStats={ride_stats} />
            <RideUtilizationChart rideStats={ride_stats} />
          </div>
          <BreakdownTable rideStats={ride_stats} />
        </section>

        {/* Section 5 */}
        <section id="stores" className="report-section">
          <h2 className="section-title">5. Store & Restaurant Analytics</h2>
          <div className="chart-grid-1">
            <StoreRevenueChart storeStats={store_stats} />
            <StoreDailyChart dailyData={daily_data} />
          </div>
        </section>

        {/* Section 6 */}
        <section id="demographics" className="report-section">
          <h2 className="section-title">6. Visitor Demographics</h2>
          <div className="chart-grid-2">
            <ArchetypePieChart archTotals={summary.archetype_totals} />
            <AvgSpendChart dailyData={daily_data} />
          </div>
          <TicketTable ticketStats={ticket_stats} />
        </section>

        {/* Section 7 */}
        <section id="weather" className="report-section">
          <h2 className="section-title">7. Weather Impact</h2>
          <WeatherTable weatherSummary={summary.weather_summary} />
        </section>

        {/* Section 8 */}
        <section id="incidents" className="report-section">
          <h2 className="section-title">8. Incidents Log</h2>
          <IncidentsTable incidents={incidents} />
        </section>

      </main>
    </div>
  )
}

function KpiCard({ label, value, highlight }) {
  return (
    <div className={`kpi-card${highlight ? ' kpi-card--highlight' : ''}`}>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
    </div>
  )
}

function DayCard({ label, day, color }) {
  return (
    <div className="day-card" style={{ borderTopColor: color }}>
      <p className="day-card-label">{label}</p>
      <p className="day-card-main">Day {day.day} &mdash; {day.day_of_week}</p>
      <p className="day-card-meta">
        <span className="weather-badge" style={{ background: W_COLORS[day.weather] }}>{day.weather}</span>
        &nbsp; {fmtNum(day.attendance)} visitors
      </p>
      <p className="day-card-revenue">{fmtMoney(day.revenue)}</p>
    </div>
  )
}

function BreakdownTable({ rideStats }) {
  const rows = Object.entries(rideStats).filter(([, s]) => s.breakdown_count > 0)
  return (
    <div className="table-block">
      <h4 className="chart-title">Ride Breakdown Summary</h4>
      {rows.length === 0
        ? <p className="empty-note">No breakdowns recorded.</p>
        : (
          <table className="data-table">
            <thead>
              <tr><th>Ride</th><th>Breakdown Count</th><th>Total Hours Down</th></tr>
            </thead>
            <tbody>
              {rows.map(([name, s]) => (
                <tr key={name}>
                  <td>{name}</td>
                  <td>{s.breakdown_count}</td>
                  <td>{s.total_breakdown_hours}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      }
    </div>
  )
}

function TicketTable({ ticketStats }) {
  const total = Object.values(ticketStats).reduce((a, s) => ({ count: a.count + s.count, revenue: a.revenue + s.revenue }), { count: 0, revenue: 0 })
  return (
    <div className="table-block">
      <h4 className="chart-title">Ticket Sales Breakdown</h4>
      <table className="data-table">
        <thead>
          <tr><th>Ticket Type</th><th>Count</th><th>Revenue</th></tr>
        </thead>
        <tbody>
          {Object.entries(ticketStats).map(([type, s]) => (
            <tr key={type}>
              <td style={{ textTransform: 'capitalize' }}>{type}</td>
              <td>{fmtNum(s.count)}</td>
              <td>{fmtMoney(s.revenue)}</td>
            </tr>
          ))}
          <tr className="table-total">
            <td>Total</td>
            <td>{fmtNum(total.count)}</td>
            <td>{fmtMoney(total.revenue)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function WeatherTable({ weatherSummary }) {
  return (
    <table className="data-table">
      <thead>
        <tr><th>Weather</th><th>Days</th><th>Avg Attendance</th><th>Avg Revenue</th></tr>
      </thead>
      <tbody>
        {Object.entries(weatherSummary).map(([state, s]) => (
          <tr key={state}>
            <td>
              <span className="weather-badge" style={{ background: W_COLORS[state] }}>{state}</span>
            </td>
            <td>{s.count}</td>
            <td>{fmtNum(Math.round(s.avg_attendance))}</td>
            <td>{fmtMoney(s.avg_revenue)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function IncidentsTable({ incidents }) {
  if (!incidents.length) {
    return <p className="empty-note">No incidents were recorded during this simulation.</p>
  }
  return (
    <table className="data-table">
      <thead>
        <tr><th>Day</th><th>Ride</th><th>Hours Affected</th></tr>
      </thead>
      <tbody>
        {incidents.map((inc, i) => (
          <tr key={i}>
            <td>{inc.day}</td>
            <td>{inc.ride}</td>
            <td>{inc.hours_down}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
