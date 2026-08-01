import { useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import Footer from '../components/Footer'
import SimCard from '../components/SimCard'
import './HomePage.css'

const FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSe2b0j7aJfSHL4qWwzLCq8aZed_SC-q5w3xUJc7GD1U4fbIBg/viewform?usp=header'

const STATS = [
  { value: '3', label: 'Revenue Streams Tracked' },
  { value: '6', label: 'Visitor Archetypes' },
  { value: '5', label: 'Downloadable File Formats' },
]

export default function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="home-page">
      <NavBar />

      <main className="home-main">

        {/* Hero */}
        <section className="hero">
          <h1 className="hero-headline">Simuleras. Simulate, Download, & Build.</h1>
          <p className="hero-sub">
            Generate realistic synthetic business data from fully simulated operations.
            Every run is unique. Download CSV, SQL, or PDF, for free.
          </p>
        </section>

        {/* Stats bar */}
        <div className="stats-bar">
          {STATS.map(s => (
            <div key={s.label} className="stat-item">
              <span className="stat-value">{s.value}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Cards grid */}
        <section className="cards-section">
          <h2 className="cards-heading">Available Simulations</h2>
          <div className="cards-grid">

            <SimCard
              title="Amusement Park"
              description="Simulate up to 365 days of amusement park operations. Rides, weather, visitor archetypes, revenue streams, and incidents, all randomized."
              tags={['Attendance', 'Revenue', 'Rides', 'Weather']}
              badge="Live"
              badgeType="live"
              btnLabel="Launch Simulation"
              onAction={() => navigate('/amusement-park')}
            />

            <SimCard
              title="Hospital"
              description="Simulate daily hospital operations including patient admissions, department throughput, staffing, and resource utilization."
              tags={['Admissions', 'Staffing', 'Departments', 'Capacity']}
              badge="Coming Soon"
              badgeType="soon"
              btnLabel="Coming Soon"
              disabled
            />

            <SimCard
              title="Suggest a Simulation"
              description="Have an idea for a simulation you'd like to see? Submit it and it might become the next one built."
              tags={['Open to ideas']}
              btnLabel="Submit Idea"
              onAction={() => window.open(FORM_URL, '_blank', 'noopener,noreferrer')}
            />

          </div>
        </section>

      </main>

      <Footer />
    </div>
  )
}
