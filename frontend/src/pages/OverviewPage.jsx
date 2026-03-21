import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LabelList,
  ResponsiveContainer,
} from 'recharts'

import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import MetricCard from '../components/ui/MetricCard'
import {
  formatCurrency,
  formatCompact,
  formatPct,
  formatNumber,
  getProfitColor,
} from '../utils/formatters'

const PIE_COLORS = [
  '#387ED1', '#21B556', '#F59E0B', '#E74C3C',
  '#8B5CF6', '#06B6D4', '#EC4899', '#84CC16',
  '#F97316', '#14B8A6', '#6366F1', '#A78BFA',
]

const TOOLTIP_STYLE = {
  backgroundColor: '#1A1A1A',
  border: '1px solid #2A2A2A',
  borderRadius: '8px',
  fontSize: '12px',
  color: '#FFFFFF',
}

function SectionLabel({ children }) {
  return (
    <p className="uppercase text-[10px] tracking-widest text-text-secondary font-medium mb-3">
      {children}
    </p>
  )
}

function fmtAxisDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })
}

// Per-bar label with profit/loss color to match the bar fill
function BarLabel({ x, y, width, height, value }) {
  const isPositive = value >= 0
  return (
    <text
      x={isPositive ? x + width + 6 : x - 6}
      y={y + height / 2}
      dy="0.35em"
      fill={getProfitColor(value)}
      fontSize={11}
      textAnchor={isPositive ? 'start' : 'end'}
    >
      {formatPct(value)}
    </text>
  )
}

function MetricSkeleton({ cols }) {
  return (
    <div className={`grid grid-cols-${cols} gap-4`}>
      {Array.from({ length: cols }).map((_, i) => (
        <Card key={i} className="p-5">
          <Loader rows={3} height="h-4" />
        </Card>
      ))}
    </div>
  )
}

export default function OverviewPage({ analytics, onAnalyse, isLoading, isError, error }) {
  if (isError) {
    return (
      <Card className="p-8 text-center">
        <p className="text-loss text-sm mb-4">
          {error?.message ?? 'Analysis failed — check that the backend is running.'}
        </p>
        <button
          onClick={onAnalyse}
          className="px-4 py-2 bg-accent text-text-primary text-sm rounded-card hover:opacity-90 transition-opacity"
        >
          Retry
        </button>
      </Card>
    )
  }

  if (isLoading || !analytics) {
    return (
      <div className="space-y-6">
        <MetricSkeleton cols={4} />
        <div className="max-w-3xl">
          <MetricSkeleton cols={3} />
        </div>
        <div className="grid grid-cols-2 gap-6">
          <Card className="p-4"><Loader rows={3} height="h-40" /></Card>
          <Card className="p-4"><Loader rows={3} height="h-40" /></Card>
        </div>
        <Card className="p-4"><Loader rows={8} height="h-5" /></Card>
      </div>
    )
  }

  const { stocks, portfolio_summary, portfolio_history } = analytics
  const {
    total_investment,
    total_current_value,
    overall_pct_return,
    portfolio_volatility,
    portfolio_sharpe,
    portfolio_max_drawdown,
    beta,
  } = portfolio_summary

  const sharpeLabel =
    portfolio_sharpe > 1 ? 'Good (>1)' : portfolio_sharpe < 0 ? 'Poor (<0)' : 'Fair'

  const betaLabel =
    beta !== null && beta !== undefined
      ? beta < 1
        ? 'Low risk (<1)'
        : 'High risk (>1)'
      : null

  const pieData = Object.entries(stocks).map(([ticker, s]) => ({
    name: ticker,
    value: s.current_value,
  }))
  const totalPieValue = pieData.reduce((sum, d) => sum + d.value, 0)

  const barData = Object.entries(stocks)
    .map(([ticker, s]) => ({ ticker, pct_return: s.pct_return }))
    .sort((a, b) => b.pct_return - a.pct_return)

  const barChartHeight = barData.length * 36

  // ~8 ticks across the history length keeps the X axis readable
  const xTickInterval = Math.max(1, Math.floor(portfolio_history.length / 8))

  return (
    <div className="space-y-6">

      {/* ── Row 1: portfolio-level metric cards ───────────────────────── */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Total Invested"
          value={formatCurrency(total_investment)}
          description="Cost basis"
        />
        <MetricCard
          label="Current Value"
          value={formatCurrency(total_current_value)}
          change={overall_pct_return}
          changeLabel="total return"
        />
        <MetricCard
          label="Total Return"
          value={formatPct(overall_pct_return)}
          change={overall_pct_return}
          description="Since inception"
        />
        <MetricCard
          label="Volatility"
          value={formatPct(portfolio_volatility * 100)}
          description="Annualised std dev"
        />
      </div>

      {/* ── Row 2: risk metric cards ───────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4 max-w-3xl">
        <MetricCard
          label="Sharpe Ratio"
          value={formatNumber(portfolio_sharpe)}
          description={`Risk-adjusted return • ${sharpeLabel}`}
        />
        <MetricCard
          label="Max Drawdown"
          value={formatPct(portfolio_max_drawdown)}
          change={portfolio_max_drawdown}
          description="Peak to trough decline"
        />
        <MetricCard
          label="Beta"
          value={beta !== null && beta !== undefined ? formatNumber(beta) : 'N/A'}
          description={
            betaLabel ? `Market sensitivity • ${betaLabel}` : 'Market sensitivity'
          }
        />
      </div>

      {/* ── Section 2: allocation donut + value area chart ─────────────── */}
      <div className="grid grid-cols-2 gap-6">

        {/* Donut — Asset Allocation */}
        <Card>
          <SectionLabel>Asset Allocation</SectionLabel>
          <div className="relative">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={90}
                  stroke="none"
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(value, name) => [formatCurrency(value), name]}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Center annotation — sits above the SVG, pointer-events off so tooltip still fires */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-text-primary font-bold text-sm">
                {formatCompact(totalPieValue)}
              </span>
              <span className="text-text-secondary text-[10px]">Portfolio</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3">
            {pieData.map((entry, i) => {
              const pct = totalPieValue > 0 ? (entry.value / totalPieValue) * 100 : 0
              return (
                <div key={entry.name} className="flex items-center gap-1">
                  <span
                    className="inline-block w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                  />
                  <span className="text-xs text-text-secondary">
                    {entry.name} {pct.toFixed(1)}%
                  </span>
                </div>
              )
            })}
          </div>
        </Card>

        {/* Area chart — Portfolio Value Over Time */}
        <Card>
          <SectionLabel>Portfolio Value</SectionLabel>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart
              data={portfolio_history}
              margin={{ top: 8, right: 72, bottom: 0, left: 0 }}
            >
              <defs>
                <linearGradient id="portfolioGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#387ED1" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#387ED1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tickFormatter={fmtAxisDate}
                tick={{ fill: '#808080', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                interval={xTickInterval}
              />
              <YAxis
                orientation="right"
                tickFormatter={formatCompact}
                tick={{ fill: '#808080', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                width={68}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(value) => [formatCurrency(value), 'Value']}
                labelFormatter={fmtAxisDate}
              />
              <ReferenceLine
                y={total_investment}
                stroke="#808080"
                strokeDasharray="4 4"
                label={{
                  value: 'Cost Basis',
                  position: 'insideTopRight',
                  fill: '#808080',
                  fontSize: 10,
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#387ED1"
                strokeWidth={2}
                fill="url(#portfolioGrad)"
                dot={false}
                activeDot={{ r: 4, fill: '#387ED1' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* ── Section 3: return by stock horizontal bar chart ────────────── */}
      <Card>
        <SectionLabel>Return by Stock</SectionLabel>
        <ResponsiveContainer width="100%" height={barChartHeight}>
          <BarChart
            data={barData}
            layout="vertical"
            margin={{ top: 0, right: 80, bottom: 0, left: 40 }}
          >
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="ticker"
              tick={{ fill: '#FFFFFF', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <ReferenceLine x={0} stroke="#2A2A2A" />
            <Bar dataKey="pct_return" barSize={16}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={getProfitColor(entry.pct_return)} />
              ))}
              <LabelList dataKey="pct_return" content={BarLabel} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

    </div>
  )
}
