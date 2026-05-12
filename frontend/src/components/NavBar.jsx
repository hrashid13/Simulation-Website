import './NavBar.css'

const FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSe2b0j7aJfSHL4qWwzLCq8aZed_SC-q5w3xUJc7GD1U4fbIBg/viewform?usp=header'

export default function NavBar() {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <span className="navbar-wordmark">Simuleras</span>
        <a
          className="navbar-suggest"
          href={FORM_URL}
          target="_blank"
          rel="noopener noreferrer"
        >
          Suggest a Sim
        </a>
      </div>
    </nav>
  )
}
