import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import MetricCard from '../components/ui/MetricCard'
import { fetchCorrelation, fetchBenchmark } from '../api/client'

const BENCHMARKS = [
  { label: 'Nifty 50', ticker: '^NSEI' },
  { label: 'S&P 500',  ticker: '^GSPC' },
  { label: 'NASDAQ',   ticker: '^IXIC' },
]

const RANGES = ['1M', '3M', '6M', '1Y']

const RANGE_MONTHS = { '1M': 1, '3M': 3, '6M': 6, '1Y': 12 }

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

function ToggleButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={
        active
          ? 'px-4 py-1.5 rounded-card text-sm font-medium bg-accent text-white border-transparent'
          : 'px-4 py-1.5 rounded-card text-sm font-medium bg-surface text-text-secondary border border-border hover:border-accent hover:text-primary transition-colors'
      }
    >
      {children}
    </button>
  )
}

function getCellBg(value) {
  if (value === 1.0)  return 'bg-accent'
  if (value >= 0.7)   return 'bg-loss/80'
  if (value >= 0.4)   return 'bg-amber/60'
  if (value >= 0.1)   return 'bg-amber/20'
  if (value >= 0)     return 'bg-surface'
  return 'bg-profit/40'
}

function getScoreColor(score) {
  if (score >= 65) return 'text-profit'
  if (score >= 40) return 'text-amber'
  return 'text-loss'
}

function fmtAxisDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })
}

function ProgressBar({ score }) {
  return (
    <div className="h-1.5 bg-border rounded-full mt-1">
      <div
        className="h-1.5 bg-accent rounded-full"
        style={{ width: `${Math.min(Math.max(score, 0), 100)}%` }}
      />
    </div>
  )
}

// ── Section 1: Correlation heatmap + diversification score ──────────────────

function CorrelationSection({ portfolio, analyticsData }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['correlation', portfolio],
    queryFn: () => fetchCorrelation(portfolio),
    staleTime: 5 * 60 * 1000,
  })

  const largestTicker = Object.entries(analyticsData?.stocks ?? {})
    .map(([t, d]) => ({ ticker: t, value: d.current_value }))
    .sort((a, b) => b.value - a.value)[0]?.ticker ?? '—'

  if (isLoading) {
    return (
      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-3">
          <Card><Loader rows={5} height="h-8" /></Card>
        </div>
        <div className="col-span-2">
          <Card><Loader rows={4} height="h-6" /></Card>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-3">
          <Card>
            <SectionLabel>Correlation Matrix</SectionLabel>
            <p className="text-loss text-sm">{error?.message ?? 'Failed to load correlation data.'}</p>
          </Card>
        </div>
        <div className="col-span-2">
          <Card>
            <SectionLabel>Diversification</SectionLabel>
            <p className="text-loss text-sm">Unavailable.</p>
          </Card>
        </div>
      </div>
    )
  }

  const { correlation_matrix: matrix, diversification: div } = data
  const tickers = Object.keys(matrix)
  const n = tickers.length

  const correlationScore   = Math.min(100, Math.max(0, (1 - div.avg_correlation) * 100))
  const concentrationScore = Math.min(100, Math.max(0, (1 - div.max_concentration) * 100))

  const scoreColor = getScoreColor(div.score)

  return (
    <div className="grid grid-cols-5 gap-6">

      {/* Left: heatmap */}
      <div className="col-span-3">
        <Card>
          <SectionLabel>Correlation Matrix</SectionLabel>
          <div
            style={{ display: 'grid', gridTemplateColumns: `repeat(${n + 1}, minmax(0, 1fr))` }}
          >
            {/* Header row */}
            <div />
            {tickers.map(t => (
              <div
                key={t}
                className="text-[11px] text-text-secondary font-medium px-2 py-1 flex items-center justify-center"
              >
                {t}
              </div>
            ))}

            {/* Data rows */}
            {tickers.map(row => (
              <>
                <div
                  key={`label-${row}`}
                  className="text-[11px] text-text-secondary font-medium px-2 py-1 flex items-center justify-center"
                >
                  {row}
                </div>
                {tickers.map(col => {
                  const val = matrix[row][col]
                  return (
                    <div
                      key={`${row}-${col}`}
                      className={`w-full aspect-square flex items-center justify-center text-[11px] font-medium text-primary rounded-sm border border-border/30 ${getCellBg(val)}`}
                    >
                      {val.toFixed(2)}
                    </div>
                  )
                })}
              </>
            ))}
          </div>
        </Card>
      </div>

      {/* Right: diversification score */}
      <div className="col-span-2">
        <Card>
          <SectionLabel>Diversification</SectionLabel>

          <div className="flex flex-col items-center pt-2 pb-4">
            <span className={`text-6xl font-bold ${scoreColor}`}>
              {Math.round(div.score)}
            </span>
            <span className={`text-sm font-medium mt-1 ${scoreColor}`}>
              {div.label}
            </span>
            <p className="text-text-secondary text-xs mt-2 text-center max-w-[200px] leading-snug line-clamp-2">
              {div.explanation}
            </p>
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-text-secondary">Correlation Component (60%)</span>
                <span className="text-xs text-text-secondary">{correlationScore.toFixed(0)}</span>
              </div>
              <ProgressBar score={correlationScore} />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-text-secondary">Concentration Component (40%)</span>
                <span className="text-xs text-text-secondary">{concentrationScore.toFixed(0)}</span>
              </div>
              <ProgressBar score={concentrationScore} />
            </div>

            <p className="text-xs text-text-secondary mt-3">
              Avg pairwise correlation: {div.avg_correlation.toFixed(2)}
            </p>
            <p className="text-xs text-text-secondary">
              Largest position: {largestTicker} at{' '}
              {(div.max_concentration * 100).toFixed(1)}%
            </p>
          </div>
        </Card>
      </div>

    </div>
  )
}

// ── Section 2: Benchmark comparison ─────────────────────────────────────────

function BenchmarkSection({ portfolio }) {
  const [selectedBenchmark, setSelectedBenchmark] = useState('^GSPC')
  const [range, setRange] = useState('1Y')

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['benchmark', portfolio, selectedBenchmark],
    queryFn: () => fetchBenchmark(portfolio, selectedBenchmark),
    staleTime: 5 * 60 * 1000,
  })

  const filteredData = useMemo(() => {
    if (!data?.comparison) return []
    const cutoff = new Date()
    cutoff.setMonth(cutoff.getMonth() - RANGE_MONTHS[range])
    return data.comparison.filter(d => new Date(d.date) >= cutoff)
  }, [data, range])

  const lastPortfolio  = filteredData.at(-1)?.portfolio_normalised ?? null
  const lastBenchmark  = filteredData.at(-1)?.benchmark_normalised ?? null
  const alpha = lastPortfolio !== null && lastBenchmark !== null
    ? lastPortfolio - lastBenchmark
    : null

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <SectionLabel>Benchmark Comparison</SectionLabel>
        {/* Range selector — right-aligned */}
        <div className="flex gap-2 -mt-3">
          {RANGES.map(r => (
            <ToggleButton key={r} active={range === r} onClick={() => setRange(r)}>
              {r}
            </ToggleButton>
          ))}
        </div>
      </div>

      {/* Benchmark selector */}
      <div className="flex gap-2 mb-4">
        {BENCHMARKS.map(b => (
          <ToggleButton
            key={b.ticker}
            active={selectedBenchmark === b.ticker}
            onClick={() => setSelectedBenchmark(b.ticker)}
          >
            {b.label}
          </ToggleButton>
        ))}
      </div>

      {isError && (
        <p className="text-loss text-sm py-8 text-center">
          {error?.message ?? 'Failed to load benchmark data.'}
        </p>
      )}

      {isLoading && <Card className="border-0 shadow-none"><Loader rows={6} height="h-6" /></Card>}

      {!isLoading && !isError && (
        <>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart
              data={filteredData}
              margin={{ top: 8, right: 56, bottom: 0, left: 0 }}
            >
              <XAxis
                dataKey="date"
                tickFormatter={fmtAxisDate}
                tick={{ fill: '#808080', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                orientation="right"
                tick={{ fill: '#808080', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={v => v.toFixed(1)}
                width={52}
              />
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(value, name) => [value.toFixed(2), name]}
                labelFormatter={fmtAxisDate}
              />
              <Legend
                verticalAlign="bottom"
                iconType="line"
                wrapperStyle={{ fontSize: '12px', paddingTop: '12px' }}
              />
              <ReferenceLine
                y={100}
                stroke="#2A2A2A"
                strokeDasharray="3 3"
              />
              <Line
                type="monotone"
                dataKey="portfolio_normalised"
                name="Portfolio"
                stroke="#387ED1"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="benchmark_normalised"
                name="Benchmark"
                stroke="#F59E0B"
                strokeWidth={1.5}
                strokeDasharray="5 5"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>

          <div className="grid grid-cols-3 gap-4 mt-4">
            <MetricCard
              label="Portfolio (Rebased)"
              value={lastPortfolio !== null ? lastPortfolio.toFixed(2) : 'N/A'}
            />
            <MetricCard
              label="Benchmark (Rebased)"
              value={lastBenchmark !== null ? lastBenchmark.toFixed(2) : 'N/A'}
            />
            <MetricCard
              label="Alpha"
              value={alpha !== null ? `${alpha >= 0 ? '+' : ''}${alpha.toFixed(2)} pts` : 'N/A'}
              change={alpha}
            />
          </div>
        </>
      )}
    </Card>
  )
}

// ── Page root ────────────────────────────────────────────────────────────────

export default function RiskPage({ portfolio, analyticsData }) {
  return (
    <div className="space-y-6">
      <CorrelationSection portfolio={portfolio} analyticsData={analyticsData} />
      <BenchmarkSection   portfolio={portfolio} />
    </div>
  )
}
