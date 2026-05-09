export const W_COLORS = { Sunny: '#F9A825', Cloudy: '#90A4AE', Rainy: '#42A5F5' }
export const REV_COLORS = ['#1565C0', '#2E7D32', '#E65100']
export const ARCH_COLORS = ['#EF5350', '#42A5F5', '#66BB6A', '#FFA726', '#AB47BC', '#26C6DA']
export const RIDE_COLOR = '#5C6BC0'
export const FB_COLOR = '#2E7D32'
export const RETAIL_COLOR = '#E65100'
export const DOW_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export const fmtMoney = v =>
  '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const fmtMoneyShort = v => {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`
  return `$${v.toFixed(0)}`
}

export const fmtNum = v => Number(v).toLocaleString('en-US')
