import { useState, useEffect, useRef } from 'react'
import { Brain, Activity, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Loader from '../components/ui/Loader'
import { fetchHealthReport, fetchSentiment, fetchCorrelation, fetchSimulation } from '../api/client'

function scoreColor(score) {
  if (score <= 40) return 'loss'
  if (score <= 70) return 'amber'
  return 'profit'
}

const SCORE_BADGE_CLASS = {
  loss:   'border-loss text-loss',
  amber:  'border-amber text-amber',
  profit: 'border-profit text-profit',
}

const SCORE_BAR_CLASS = {
  loss:   'bg-loss',
  amber:  'bg-amber',
  profit: 'bg-profit',
}

const SENTIMENT_VARIANT = {
  positive: 'profit',
  neutral:  'neutral',
  negative: 'loss',
}

const SENTIMENT_BORDER_L = {
  profit:  'border-l-profit',
  neutral: 'border-l-text-secondary',
  loss:    'border-l-loss',
}

function SectionLabel({ children }) {
  return (
    <p className="uppercase text-[10px] tracking-widest text-text-secondary font-medium mb-3">
      {children}
    </p>
  )
}

function TickerSentimentCard({ ticker, data }) {
  const { overall_sentiment, sentiment_score, headlines_analysed, headlines = [] } = data
  const variant  = SENTIMENT_VARIANT[overall_sentiment] ?? 'neutral'
  const borderL  = SENTIMENT_BORDER_L[variant]
  const visible  = headlines.slice(0, 2)
  const extra    = headlines.length - 2

  return (
    <div className={clsx('bg-surface border border-border border-l-4 rounded-card p-4', borderL)}>
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold text-sm text-primary">{ticker}</span>
        <Badge label={overall_sentiment} variant={variant} />
      </div>

      <p className="text-xs text-text-secondary mb-1">
        Score: {sentiment_score > 0 ? '+' : ''}{sentiment_score.toFixed(3)}
      </p>
      <p className="text-xs text-text-secondary mb-2">
        {headlines_analysed} headlines analysed
      </p>

      <div>
        {visible.map((h, i) => (
          <p
            key={i}
            className="text-xs text-text-secondary py-1 border-b border-border last:border-0 truncate"
          >
            • {h.headline.slice(0, 65)}...
          </p>
        ))}
        {extra > 0 && (
          <p className="text-xs text-accent cursor-pointer mt-1">+{extra} more</p>
        )}
      </div>
    </div>
  )
}

export default function InsightsPage({ analytics, portfolio }) {
  const [healthData,      setHealthData]      = useState(null)
  const [reportLoading,   setReportLoading]   = useState(false)
  const [reportError,     setReportError]     = useState(null)
  const [animatedScore,   setAnimatedScore]   = useState(0)

  const [sentimentData,    setSentimentData]    = useState(null)
  const [sentimentLoading, setSentimentLoading] = useState(false)
  const [sentimentError,   setSentimentError]   = useState(null)

  // Cache on-demand fetches so re-generating the report skips redundant calls
  const correlationCache = useRef(null)
  const simulationCache  = useRef(null)

  // Trigger CSS width transition one paint cycle after data arrives
  useEffect(() => {
    if (!healthData) return
    setAnimatedScore(0)
    const id = setTimeout(() => setAnimatedScore(healthData.health_score), 50)
    return () => clearTimeout(id)
  }, [healthData])

  async function handleGenerateReport() {
    setReportLoading(true)
    setReportError(null)
    try {
      const [corrResult, simResult] = await Promise.all([
        correlationCache.current
          ? Promise.resolve(correlationCache.current)
          : fetchCorrelation(portfolio).then(r => { correlationCache.current = r; return r }),
        simulationCache.current
          ? Promise.resolve(simulationCache.current)
          : fetchSimulation(portfolio).then(r => { simulationCache.current = r; return r }),
      ])

      const payload = {
        portfolio_summary:  analytics.portfolio_summary,
        diversification:    corrResult.diversification,
        simulation_summary: simResult.summary,
      }

      const result = await fetchHealthReport(payload)
      setHealthData(result)
    } catch (err) {
      setReportError(err?.response?.data?.detail ?? err?.message ?? 'Failed to generate report.')
    } finally {
      setReportLoading(false)
    }
  }

  async function handleRunSentiment() {
    setSentimentLoading(true)
    setSentimentError(null)
    try {
      const tickers_and_names = portfolio.reduce(
        (acc, h) => ({ ...acc, [h.ticker]: h.ticker }),
        {}
      )
      const result = await fetchSentiment(tickers_and_names)
      setSentimentData(result)
    } catch (err) {
      setSentimentError(err?.response?.data?.detail ?? err?.message ?? 'Failed to run sentiment analysis.')
    } finally {
      setSentimentLoading(false)
    }
  }

  const color = healthData ? scoreColor(healthData.health_score) : 'profit'

  const positiveCount = sentimentData
    ? Object.values(sentimentData.ticker_sentiments).filter(t => t.overall_sentiment === 'positive').length
    : 0
  const totalTickers = sentimentData
    ? Object.keys(sentimentData.ticker_sentiments).length
    : 0

  return (
    <div className="space-y-6">

      {/* ── Section 1: AI Health Report ── */}
      <Card>
        <SectionLabel>Portfolio Health Report</SectionLabel>

        <button
          onClick={handleGenerateReport}
          disabled={!analytics || reportLoading}
          className={clsx(
            'bg-accent text-white rounded-card px-6 py-2.5 font-medium text-sm transition-opacity mb-4 flex items-center gap-2',
            (!analytics || reportLoading) && 'opacity-50 cursor-not-allowed'
          )}
        >
          {reportLoading
            ? <><Loader2 size={14} className="animate-spin" /> Generating…</>
            : 'Generate Report'
          }
        </button>

        {reportLoading && <Loader rows={5} height="h-5" />}

        {!reportLoading && reportError && (
          <p className="text-loss text-sm">{reportError}</p>
        )}

        {!reportLoading && !reportError && !healthData && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <Brain size={36} className="mb-3 opacity-40 text-text-secondary" />
            <p className="text-sm text-text-secondary">No report generated yet.</p>
            <p className="text-sm text-text-secondary mt-1">
              Click Generate Report to analyse your portfolio.
            </p>
          </div>
        )}

        {!reportLoading && healthData && (
          <div>
            {/* Header: title + score circle */}
            <div className="flex justify-between items-center mb-4">
              <span className="font-semibold text-base text-primary">Portfolio Health Report</span>
              <div className="flex flex-col items-center">
                <div
                  className={clsx(
                    'w-20 h-20 rounded-full border-4 flex items-center justify-center font-bold text-2xl mx-auto mb-1',
                    SCORE_BADGE_CLASS[color]
                  )}
                >
                  {healthData.health_score}
                </div>
                <span className="text-xs text-text-secondary">{healthData.health_label}</span>
              </div>
            </div>

            {/* Progress bar */}
            <div className="h-2 bg-border rounded-full overflow-hidden mb-4">
              <div
                className={clsx('h-full rounded-full transition-all duration-700', SCORE_BAR_CLASS[color])}
                style={{ width: `${animatedScore}%` }}
              />
            </div>

            {/* Summary */}
            <div className="p-3 bg-background rounded-card border border-border mb-4">
              <p className="text-sm text-text-secondary leading-relaxed">{healthData.summary}</p>
            </div>

            {/* Risk factors + Suggestions */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface border border-border rounded-card p-4">
                <p className="uppercase text-[10px] tracking-widest text-loss font-medium mb-2">
                  ⚠ Risk Factors
                </p>
                {healthData.risk_factors.map((risk, i) => (
                  <div key={i} className="flex gap-2 items-start py-2 border-b border-border last:border-0">
                    <span className="text-loss text-xs mt-0.5">•</span>
                    <span className="text-sm text-text-secondary">{risk}</span>
                  </div>
                ))}
              </div>

              <div className="bg-surface border border-border rounded-card p-4">
                <p className="uppercase text-[10px] tracking-widest text-accent font-medium mb-2">
                  💡 Suggestions
                </p>
                {healthData.suggestions.map((s, i) => (
                  <div key={i} className="flex gap-2 items-start py-2 border-b border-border last:border-0">
                    <span className="text-accent text-xs mt-0.5">✓</span>
                    <span className="text-sm text-text-secondary">{s}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* ── Section 2: Sentiment Analysis ── */}
      <Card>
        <SectionLabel>News Sentiment</SectionLabel>

        {/* FinBERT warning — always visible */}
        <div className="bg-amber/10 border border-amber/20 rounded-card p-3 mb-4 text-amber text-xs">
          ⚠ First run downloads FinBERT (~500MB) and may take 60-90 seconds. Subsequent runs are instant.
        </div>

        <button
          onClick={handleRunSentiment}
          disabled={sentimentLoading}
          className={clsx(
            'bg-accent text-white rounded-card px-6 py-2.5 font-medium text-sm transition-opacity mb-4 flex items-center gap-2',
            sentimentLoading && 'opacity-50 cursor-not-allowed'
          )}
        >
          {sentimentLoading
            ? <><Loader2 size={14} className="animate-spin" /> Analysing…</>
            : 'Run Sentiment Analysis'
          }
        </button>

        {sentimentLoading && <Loader rows={4} height="h-5" />}

        {!sentimentLoading && sentimentError && (
          <p className="text-loss text-sm">{sentimentError}</p>
        )}

        {!sentimentLoading && !sentimentError && !sentimentData && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <Activity size={36} className="mb-3 opacity-40 text-text-secondary" />
            <p className="text-sm text-text-secondary">No sentiment data yet.</p>
            <p className="text-sm text-text-secondary mt-1">
              Run analysis to view sentiment for your holdings.
            </p>
          </div>
        )}

        {!sentimentLoading && sentimentData && (
          <div>
            {/* Portfolio-level sentiment summary */}
            <div className="flex flex-col items-center mb-6">
              <Badge
                label={sentimentData.portfolio_sentiment.toUpperCase()}
                variant={SENTIMENT_VARIANT[sentimentData.portfolio_sentiment] ?? 'neutral'}
              />
              <p className="text-text-secondary text-sm mt-2">
                {positiveCount}/{totalTickers} holdings show positive sentiment
              </p>
            </div>

            {/* Per-ticker grid */}
            <div className="grid grid-cols-3 gap-4 mt-4">
              {Object.entries(sentimentData.ticker_sentiments).map(([ticker, data]) => (
                <TickerSentimentCard key={ticker} ticker={ticker} data={data} />
              ))}
            </div>
          </div>
        )}
      </Card>

    </div>
  )
}
