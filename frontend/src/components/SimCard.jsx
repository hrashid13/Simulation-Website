import './SimCard.css'

export default function SimCard({ title, description, tags, badge, badgeType, btnLabel, onAction, disabled }) {
  return (
    <div className={`sim-card${disabled ? ' sim-card--muted' : ''}`}>
      <div className="sim-card-top">
        <h3 className="sim-card-title">{title}</h3>
        {badge && (
          <span className={`sim-badge sim-badge--${badgeType}`}>{badge}</span>
        )}
      </div>

      <p className="sim-card-desc">{description}</p>

      <div className="sim-card-tags">
        {tags.map(tag => (
          <span key={tag} className="sim-tag">{tag}</span>
        ))}
      </div>

      <button
        className={`sim-card-btn${disabled ? ' sim-card-btn--disabled' : ''}`}
        onClick={onAction}
        disabled={disabled}
      >
        {btnLabel}
      </button>
    </div>
  )
}
