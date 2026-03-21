import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import MetricCard from '../components/ui/MetricCard'
import Badge from '../components/ui/Badge'
import { fetchSimulation } from '../api/client'
import { formatCurrency, formatCompact, formatPct } from '../utils/formatters'

const X_TICKS = [0, 63, 126, 189, 252]

const RISK_VARIANT = {
  'Low Risk':      'profit',
  'Moderate Risk': 'amber',
  'High Risk':     'loss',
}

function SectionLabel({ children }) {
  return (
    <p className="uppercase text-[10px] tracking-widest text-text-secondary font-medium mb-3">
      {children}
    </p>
  )
}

function findClosestPath(paths, target) {
  return paths.reduce((bestIdx, path, idx) =>
    Math.abs(path[252] - target) < Math.abs(paths[bestIdx][252] - target) ? idx : bestIdx
  , 0)
}

function SimulationTooltip({ payload }) {
  const relevant = payload?.filter(p =>
    ['lineP10', 'lineP50', 'lineP90'].includes(p.dataKey)
  )
  if (!relevant?.length) return null
  return (
    <div className="bg-surface border border-border rounded-card p-2 text-xs">
      {relevant.map(p => (
        <div key={p.dataKey} style={{ color: p.color }}>
          {p.dataKey === 'lineP10' ? 'Bear' :
           p.dataKey === 'lineP50' ? 'Base' : 'Bull'}
          : {formatCurrency(p.value)}
        </div>
      ))}
    </div>
  )
}

function SimulationChart({ data: simulationData }) {
  const { percentiles } = simulationData

  const combinedData = useMemo(() => {
    if (!simulationData?.paths_sample) return []
    const { paths_sample, percentiles } = simulationData
    const nDays = paths_sample.length        // 253
    const nPaths = paths_sample[0].length    // 50

    const finalValues = Array.from({ length: nPaths },
      (_, p) => paths_sample[nDays - 1][p])

    const findClosest = (target) =>
      finalValues.reduce((bestIdx, val, idx) =>
        Math.abs(val - target) < Math.abs(finalValues[bestIdx] - target)
          ? idx : bestIdx
      , 0)

    const p10Idx = findClosest(percentiles.p10)
    const p50Idx = findClosest(percentiles.p50)
    const p90Idx = findClosest(percentiles.p90)

    return Array.from({ length: nDays }, (_, d) => {
      const obj = { day: d }
      for (let p = 0; p < Math.min(30, nPaths); p++) {
        if (p !== p10Idx && p !== p50Idx && p !== p90Idx) {
          obj[`bg${p}`] = paths_sample[d][p]
        }
      }
      obj.lineP10 = paths_sample[d][p10Idx]
      obj.lineP50 = paths_sample[d][p50Idx]
      obj.lineP90 = paths_sample[d][p90Idx]
      return obj
    })
  }, [simulationData])

  return (
    <Card>
      <SectionLabel>Monte Carlo Simulation</SectionLabel>
      <p className="text-text-secondary text-xs mb-4">
        1,000 simulated paths · 252 trading days
      </p>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={combinedData}
          margin={{ top: 8, right: 80, bottom: 28, left: 0 }}
        >
          <XAxis
            dataKey="day"
            domain={[0, 252]}
            ticks={X_TICKS}
            tick={{ fill: '#808080', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            label={{
              value: 'Trading Days',
              position: 'insideBottom',
              offset: -14,
              fill: '#808080',
              fontSize: 11,
            }}
          />
          <YAxis
            orientation="right"
            tickFormatter={formatCompact}
            domain={[
              simulationData.percentiles.p10 * 0.85,
              simulationData.percentiles.p90 * 1.15,
            ]}
            tick={{ fill: '#808080', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={92}
          />
          <Tooltip content={<SimulationTooltip />} />
          <ReferenceLine
            y={percentiles.current_value}
            stroke="#387ED1"
            strokeDasharray="4 4"
            label={{
              value: 'Today',
              position: 'insideTopLeft',
              fill: '#387ED1',
              fontSize: 11,
            }}
          />

          {/* Background sample paths — animation off for perf */}
          {Array.from({ length: 30 }, (_, i) => (
            <Line
              key={`bg${i}`}
              dataKey={`bg${i}`}
              stroke="#2A2A2A"
              strokeWidth={1}
              strokeOpacity={0.5}
              dot={false}
              activeDot={false}
              isAnimationActive={false}
            />
          ))}

          {/* Percentile overlay lines */}
          <Line
            dataKey="lineP10"
            stroke="#E74C3C"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            dataKey="lineP50"
            stroke="#F59E0B"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            dataKey="lineP90"
            stroke="#21B556"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )
}

export default function SimulationPage({ portfolio }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['simulation', portfolio],
    queryFn: () => fetchSimulation(portfolio),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }, (_, i) => (
            <Card key={i}><Loader rows={3} height="h-5" /></Card>
          ))}
        </div>
        <Card><Loader rows={8} height="h-6" /></Card>
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 3 }, (_, i) => (
            <Card key={i}><Loader rows={3} height="h-5" /></Card>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-loss text-sm">
          {error?.message ?? 'Failed to load simulation data.'}
        </p>
      </div>
    )
  }

  if (!data) return null

  const { summary, percentiles } = data
  const riskVariant = RISK_VARIANT[summary.risk_label] ?? 'neutral'

  return (
    <div className="space-y-6">

      {/* Section 1 — Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Current Value"
          value={formatCurrency(percentiles.current_value)}
          description="Portfolio today"
        />
        <MetricCard
          label="Median Outcome"
          value={formatCurrency(percentiles.p50)}
          description="Base case (252 days)"
        />
        <MetricCard
          label="Best Case (P90)"
          value={<span className="text-profit">{formatCurrency(percentiles.p90)}</span>}
          description="Bull case"
        />
        <MetricCard
          label="Worst Case (P10)"
          value={<span className="text-loss">{formatCurrency(percentiles.p10)}</span>}
          description="Bear case"
        />
      </div>

      {/* Section 2 — Simulation chart */}
      <SimulationChart data={data} />

      {/* Section 3 — Risk metrics */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="Value at Risk (95%)"
          value={<span className="text-loss">{formatCurrency(summary.var_95)}</span>}
          description="Max loss at 95% confidence"
        />
        <MetricCard
          label="Probability of Profit"
          value={
            <span className={summary.prob_profit > 50 ? 'text-profit' : 'text-loss'}>
              {formatPct(summary.prob_profit)}
            </span>
          }
          description="Paths ending above current value"
        />
        <MetricCard
          label="Risk Profile"
          value={<Badge label={summary.risk_label} variant={riskVariant} />}
          description="Based on annualised volatility"
        />
      </div>

    </div>
  )
}
