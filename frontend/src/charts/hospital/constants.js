// Hospital chart palette.
//
// These are the dark-mode steps of the validated reference palette, checked with
// the data-viz validator against this app's actual chart surface (#0f1117):
//   6 department hues - lightness band PASS, chroma PASS, contrast PASS
//   3-series flow     - worst adjacent CVD dE 61.6, all PASS
//   2-series finance  - worst adjacent CVD dE 97.3, all PASS
//   occupancy ramp    - monotone, single hue, PASS
//
// The full six-department set carries a CVD warning (green vs amber, dE 10.3 —
// the floor band), and reordering the slots only makes it worse. So no chart
// ever plots all six as overlapping lines: department comparisons use small
// multiples or the heatmap, where each mark is separated by position rather
// than by hue alone.

export const DEPT_COLORS = {
  emergency_room: '#3987e5',
  radiology_lab: '#199e70',
  surgery: '#c98500',
  icu: '#008300',
  general_ward: '#9085e9',
  outpatient_clinic: '#e66767',
}

export const DEPT_ORDER = [
  'emergency_room',
  'radiology_lab',
  'surgery',
  'icu',
  'general_ward',
  'outpatient_clinic',
]

// ESI 1 (most severe) is brightest against the dark surface, fading to ESI 5.
export const ESI_COLORS = {
  1: '#cde2fb',
  2: '#9ec5f4',
  3: '#6da7ec',
  4: '#3987e5',
  5: '#256abf',
}

// Low occupancy sits near the surface and bright means full, so the ramp runs
// dark to light on a dark background.
export const OCCUPANCY_RAMP = ['#184f95', '#256abf', '#3987e5', '#6da7ec', '#9ec5f4', '#cde2fb']

export const FLOW_COLORS = {
  arrivals: '#3987e5',
  discharges: '#199e70',
  admissions: '#9085e9',
}

export const REVENUE_COLOR = '#3987e5'
export const COST_COLOR = '#d95926'
export const DIVERSION_COLOR = '#e66767'

export const EVENT_COLORS = {
  'Normal Day': '#8b90a0',
  'Seasonal Surge': '#c98500',
  'Staffing Shortage': '#9085e9',
  'Mass Casualty': '#e66767',
}

export const GRID_COLOR = '#2a2d3a'
export const TICK_STYLE = { fontSize: 11, fill: '#8b90a0' }

export const fmtNum = v => Number(v).toLocaleString('en-US')

export const fmtMoney = v => {
  const n = Number(v)
  const sign = n < 0 ? '-' : ''
  return `${sign}$${Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

export const fmtMoneyShort = v => {
  const n = Number(v)
  const sign = n < 0 ? '-' : ''
  const a = Math.abs(n)
  if (a >= 1_000_000) return `${sign}$${(a / 1_000_000).toFixed(1)}M`
  if (a >= 1_000) return `${sign}$${(a / 1_000).toFixed(0)}K`
  return `${sign}$${a.toFixed(0)}`
}

export const fmtPct = v => `${Number(v).toFixed(1)}%`

// Minutes read as minutes up to 90, then as hours — an ICU boarding delay of
// 2,046 minutes is not a number anyone can parse at a glance.
export const fmtDuration = v => {
  const n = Number(v)
  if (n < 90) return `${Math.round(n)}m`
  return `${(n / 60).toFixed(1)}h`
}

// Keep the x axis readable as the run length grows.
export const dayInterval = len =>
  len <= 14 ? 0 : len <= 30 ? 3 : len <= 90 ? 13 : len <= 180 ? 29 : 59
