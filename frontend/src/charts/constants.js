// Colors aligned with the Simuleras design system
export const W_COLORS = { Sunny: '#f59e0b', Cloudy: '#64748b', Rainy: '#4f8ef7' }
export const REV_COLORS = ['#4f8ef7', '#3ecf8e', '#f59e0b']   // blue, green, amber
export const ARCH_COLORS = ['#4f8ef7', '#3ecf8e', '#f59e0b', '#f87171', '#a78bfa', '#34d399']
export const RIDE_COLOR = '#4f8ef7'
export const FB_COLOR   = '#3ecf8e'
export const RETAIL_COLOR = '#f59e0b'

// Shared Recharts axis/grid props for the dark theme
export const GRID_COLOR  = '#2a2d3a'
export const TICK_STYLE  = { fontSize: 11, fill: '#8b90a0' }

export const DOW_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export const fmtMoney = v =>
  '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const fmtMoneyShort = v => {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`
  return `$${v.toFixed(0)}`
}

export const fmtNum = v => Number(v).toLocaleString('en-US')
