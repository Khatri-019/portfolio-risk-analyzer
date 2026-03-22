export const formatCurrency = (value, symbol = '$') => {
     if (value === null || value === undefined) return 'N/A'
     const num = Number(value)
     if (isNaN(num)) return 'N/A'
     const formatted = Math.abs(num).toLocaleString('en-US', {
       minimumFractionDigits: 2,
       maximumFractionDigits: 2,
     })
     return `${num < 0 ? '-' : ''}${symbol}${formatted}`
   }

export const formatCompact = (value, symbol = '$') => {
  // Compact formatting for large numbers in tight spaces
  // 1234567 → ₹12.3L (lakhs)
  // 12345678 → ₹1.2Cr (crores)
  // Used in TopBar where space is limited
  if (value === null || value === undefined) return 'N/A'
  if (Math.abs(value) >= 10000000)
    return `${symbol}${(value / 10000000).toFixed(1)}B`
  if (Math.abs(value) >= 100000)
    return `${symbol}${(value / 100000).toFixed(1)}M`

  if (Math.abs(value) >= 1000)                           // ← ADD THIS
    return `${symbol}${(value / 1000).toFixed(1)}K`      // ← ADD THIS
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
