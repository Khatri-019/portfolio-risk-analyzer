import { formatCompact, formatPct, getProfitClass } from '../../utils/formatters'

const SECTION_TITLES = {
  overview:   'Overview',
  holdings:   'Holdings',
  risk:       'Risk & Correlation',
  simulation: 'Simulation',
  rebalancer: 'Rebalancer',
  insights:   'AI Insights',
}

function getMarketStatus() {
  const now = new Date()
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    weekday: 'short',
    hour:    'numeric',
    minute:  'numeric',
    hour12:  false,
  }).formatToParts(now)

  const get = (type) => parts.find(p => p.type === type)?.value ?? ''

  const weekday = get('weekday')
  const hour    = parseInt(get('hour'), 10)
  const minute  = parseInt(get('minute'), 10)

  const isWeekday  = !['Sat', 'Sun'].includes(weekday)
  const minuteOfDay = hour * 60 + minute
  const isOpen = isWeekday && minuteOfDay >= 570 && minuteOfDay < 960 // 09:30–16:00

  return isOpen
}

export default function TopBar({ analytics, activeNav }) {
  const isOpen   = getMarketStatus()
  const summary  = analytics?.portfolio_summary
  const gainLoss = summary?.total_gain_loss

  return (
    <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6 shrink-0">

      <h1 className="font-semibold text-base text-text-primary">
        {SECTION_TITLES[activeNav] ?? 'Overview'}
      </h1>

      <div className="flex items-center gap-6">
        {summary && (
          <>
            <span className="text-text-primary font-bold text-lg">
              {formatCompact(summary.total_current_value)}
            </span>
            <span className={`text-sm font-medium ${getProfitClass(gainLoss)}`}>
              {formatCompact(gainLoss)}{' '}
              <span className="text-text-secondary font-normal">
                ({formatPct(summary.overall_pct_return)})
              </span>
            </span>
          </>
        )}

        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${isOpen ? 'bg-profit animate-pulse' : 'bg-text-secondary'}`}
          />
          <span className={`text-xs ${isOpen ? 'text-profit' : 'text-text-secondary'}`}>
            {isOpen ? 'Market Open' : 'Market Closed'}
          </span>
        </div>
      </div>
    </header>
  )
}
