import { useState, useEffect, useRef, useMemo } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Briefcase, ArrowRight } from 'lucide-react'
import clsx from 'clsx'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import { fetchRebalance } from '../api/client'
import { formatCurrency } from '../utils/formatters'

const ACTION_VARIANT = {
  SELL: 'loss',
  BUY:  'profit',
  HOLD: 'neutral',
}

const ACTION_BORDER = {
  SELL: 'border-loss/30 border-l-4 border-l-loss',
  BUY:  'border-profit/30 border-l-4 border-l-profit',
  HOLD: 'border-border border-l-4 border-l-text-secondary',
}

function SectionLabel({ children }) {
  return (
    <p className="uppercase text-[10px] tracking-widest text-text-secondary font-medium mb-3">
      {children}
    </p>
  )
}

function TradeCard({ trade }) {
  const { ticker, action, trade_value, trade_shares, current_weight_pct, target_weight_pct } = trade

  return (
    <div className={clsx('bg-surface border rounded-card p-4', ACTION_BORDER[action])}>
      <div className="flex items-center justify-between mb-3">
        <Badge label={action} variant={ACTION_VARIANT[action]} />
        <span className="font-semibold text-sm text-primary">{ticker}</span>
      </div>

      <p className="text-lg font-bold text-primary mb-0.5">
        {formatCurrency(Math.abs(trade_value))}
      </p>
      <p className="text-xs text-text-secondary mb-3">
        {Math.abs(trade_shares).toFixed(2)} shares
      </p>

      <div className="flex items-center gap-1.5 text-xs">
        <span className="text-text-secondary">{current_weight_pct.toFixed(1)}%</span>
        <ArrowRight size={11} className="text-text-secondary" />
        <span className="text-primary font-medium">{target_weight_pct.toFixed(1)}%</span>
      </div>
    </div>
  )
}

function deriveWeights(analyticsData) {
  const entries = Object.entries(analyticsData.stocks)
  const total = entries.reduce((s, [, d]) => s + d.current_value, 0)
  return Object.fromEntries(
    entries.map(([ticker, d]) => [
      ticker,
      parseFloat(((d.current_value / total) * 100).toFixed(1)),
    ])
  )
}

export default function RebalancerPage({ analyticsData, portfolio }) {
  const [targetWeights, setTargetWeights] = useState({})
  const seeded = useRef(false)

  useEffect(() => {
    if (analyticsData && !seeded.current) {
      seeded.current = true
      setTargetWeights(deriveWeights(analyticsData))
    }
  }, [analyticsData])

  const currentWeights = useMemo(
    () => (analyticsData ? deriveWeights(analyticsData) : {}),
    [analyticsData]
  )

  const total = useMemo(
    () => parseFloat(Object.values(targetWeights).reduce((s, v) => s + v, 0).toFixed(1)),
    [targetWeights]
  )
  const isValid = Math.abs(total - 100) <= 0.01

  const { mutate, data: rebalanceData, isPending, isError, error } = useMutation({
    mutationFn: () => fetchRebalance(portfolio, targetWeights),
  })

  function handleChange(ticker, raw) {
    const val = Math.min(100, Math.max(0, parseFloat(raw) || 0))
    setTargetWeights(prev => ({ ...prev, [ticker]: val }))
  }

  if (!analyticsData) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-text-secondary">
        <Briefcase size={32} className="mb-3 opacity-40" />
        <p className="text-sm">No portfolio data available.</p>
        <p className="text-xs mt-1 opacity-60">
          Add stocks in the sidebar and click Analyse.
        </p>
      </div>
    )
  }

  const tickers = Object.keys(analyticsData.stocks)

  const sells = rebalanceData?.trades.filter(t => t.action === 'SELL' && Math.abs(t.trade_value) >= 1.0) ?? []
  const buys  = rebalanceData?.trades.filter(t => t.action === 'BUY'  && Math.abs(t.trade_value) >= 1.0) ?? []
  const holds = rebalanceData?.trades.filter(t => t.action === 'HOLD' || Math.abs(t.trade_value) < 1.0)  ?? []

  return (
    <div className="space-y-6">

      {/* Section 1 — Target allocation input */}
      <Card>
        <SectionLabel>Target Allocation</SectionLabel>

        <div className="space-y-1">
          {tickers.map(ticker => (
            <div
              key={ticker}
              className="grid grid-cols-[80px_1fr_80px_100px] gap-3 items-center py-2"
            >
              <span className="font-semibold text-sm text-primary">{ticker}</span>

              <input
                type="range"
                min={0}
                max={100}
                step={0.5}
                value={targetWeights[ticker] ?? 0}
                onChange={e => handleChange(ticker, e.target.value)}
                className="w-full h-1 rounded-full appearance-none cursor-pointer accent-accent bg-border"
              />

              <input
                type="number"
                min={0}
                max={100}
                step={0.5}
                value={targetWeights[ticker] ?? 0}
                onChange={e => handleChange(ticker, e.target.value)}
                className="bg-surface border border-border rounded-card px-2 py-1 text-sm text-right w-full focus:border-accent focus:outline-none"
              />

              <span className="text-xs text-text-secondary">
                now: {(currentWeights[ticker] ?? 0).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>

        {/* Total counter */}
        <div className="border-t border-border pt-3 mt-2 flex justify-between items-center">
          <span className="text-sm text-text-secondary">Total Allocation</span>
          <span className={clsx('font-bold text-base', isValid ? 'text-profit' : 'text-loss')}>
            {total.toFixed(1)}%
          </span>
        </div>

        <button
          onClick={() => mutate()}
          disabled={!isValid || isPending}
          className={clsx(
            'mt-4 w-full bg-accent text-white rounded-card py-2.5 font-medium text-sm transition-opacity',
            (!isValid || isPending) && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isPending ? 'Calculating…' : 'Calculate Rebalance'}
        </button>

        {isError && (
          <p className="mt-3 text-loss text-sm text-center">
            {error?.response?.data?.detail ?? error?.message ?? 'Failed to calculate rebalance.'}
          </p>
        )}
      </Card>

      {/* Section 2 — Trade instructions */}
      {rebalanceData && (
        <div className="space-y-4">

          {/* Summary row */}
          <div className="flex gap-6">
            <div>
              <p className="text-xs text-text-secondary mb-0.5">Total to Buy</p>
              <p className="font-semibold text-profit">{formatCurrency(rebalanceData.total_buy_value)}</p>
            </div>
            <div>
              <p className="text-xs text-text-secondary mb-0.5">Total to Sell</p>
              <p className="font-semibold text-loss">{formatCurrency(rebalanceData.total_sell_value)}</p>
            </div>
          </div>

          {/* SELL + BUY cards */}
          {(sells.length > 0 || buys.length > 0) && (
            <div className="grid grid-cols-2 gap-3">
              {[...sells, ...buys].map(trade => (
                <TradeCard key={trade.ticker} trade={trade} />
              ))}
            </div>
          )}

          {/* HOLD cards */}
          {holds.length > 0 && (
            <div className="grid grid-cols-3 gap-3">
              {holds.map(trade => (
                <TradeCard key={trade.ticker} trade={trade} />
              ))}
            </div>
          )}

        </div>
      )}

    </div>
  )
}
