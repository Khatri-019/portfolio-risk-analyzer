export const formatCurrency = (value, symbol = '₹') => {
  if (value === null || value === undefined) return 'N/A'
  const [intPart, decPart] = Math.abs(value).toFixed(2).split('.')
  const lastThree = intPart.slice(-3)
  const rest = intPart.slice(0, -3)
  const formatted = rest
    ? rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + lastThree
    : lastThree
  return `${value < 0 ? '-' : ''}${symbol}${formatted}.${decPart}`
}

export const formatCompact = (value, symbol = '₹') => {
  // Compact formatting for large numbers in tight spaces
  // 1234567 → ₹12.3L (lakhs)
  // 12345678 → ₹1.2Cr (crores)
  // Used in TopBar where space is limited
  if (value === null || value === undefined) return 'N/A'
  if (Math.abs(value) >= 10000000)
    return `${symbol}${(value / 10000000).toFixed(1)}Cr`
  if (Math.abs(value) >= 100000)
    return `${symbol}${(value / 100000).toFixed(1)}L`
  return formatCurrency(value, symbol)
}

export const formatPct = (value) => {
  if (value === null || value === undefined) return 'N/A'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

export const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A'
  return Number(value).toFixed(decimals)
}

export const getProfitColor = (value) => {
  if (!value && value !== 0) return '#808080'
  if (value > 0) return '#21B556'
  if (value < 0) return '#E74C3C'
  return '#808080'
}

export const getProfitClass = (value) => {
  if (!value && value !== 0) return 'text-text-secondary'
  if (value > 0) return 'text-profit'
  if (value < 0) return 'text-loss'
  return 'text-text-secondary'
}
