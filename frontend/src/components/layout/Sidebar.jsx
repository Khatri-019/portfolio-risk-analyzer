import { useState } from 'react'
import {
  LayoutDashboard,
  Briefcase,
  Activity,
  TrendingUp,
  RefreshCw,
  Brain,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { usePortfolioStore } from '../../store/portfolioStore'
import { usePortfolioActions } from '../../hooks/usePortfolio'

const NAV_ITEMS = [
  { id: 'overview',   label: 'Overview',          icon: LayoutDashboard },
  { id: 'holdings',   label: 'Holdings',           icon: Briefcase       },
  { id: 'risk',       label: 'Risk & Correlation', icon: Activity        },
  { id: 'simulation', label: 'Simulation',         icon: TrendingUp      },
  { id: 'rebalancer', label: 'Rebalancer',         icon: RefreshCw       },
  { id: 'insights',   label: 'AI Insights',        icon: Brain           },
]

export default function Sidebar({ onAnalyse, isLoading }) {
  const { state, dispatch } = usePortfolioStore()
  const { addHolding, removeHolding } = usePortfolioActions()

  const [collapsed, setCollapsed] = useState(false)
  const [ticker, setTicker]       = useState('')
  const [quantity, setQuantity]   = useState('')
  const [buyPrice, setBuyPrice]   = useState('')

  const activeNav = state.activeNav
  const portfolio = state.portfolio

  function addStock() {
    const qty   = parseFloat(quantity)
    const price = parseFloat(buyPrice)
    if (!ticker.trim() || isNaN(qty) || isNaN(price) || qty <= 0 || price <= 0) return
    addHolding({ ticker: ticker.trim().toUpperCase(), quantity: qty, buy_price: price })
    setTicker('')
    setQuantity('')
    setBuyPrice('')
  }

  return (
    <div className="flex-shrink-0 h-screen">

      {collapsed ? (

        /* ── COLLAPSED: icon rail only ─────────────────────────────── */
        <div className="w-14 flex flex-col items-center py-4 gap-1 bg-background border-r border-border h-full">

          <button
            onClick={() => setCollapsed(false)}
            className="p-2 rounded-card text-text-secondary hover:text-text-primary hover:bg-surface transition-colors mb-3"
          >
            <ChevronRight size={15} />
          </button>

          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => dispatch({ type: 'SET_ACTIVE_NAV', payload: id })}
              title={label}
              className={`p-2 rounded-card transition-colors w-10 flex items-center justify-center ${
                activeNav === id
                  ? 'bg-surface text-accent'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface'
              }`}
            >
              <Icon size={16} />
            </button>
          ))}
        </div>

      ) : (

        /* ── EXPANDED: full panel only, no icon rail ────────────────── */
        <div className="w-64 flex flex-col h-screen overflow-hidden bg-background border-r border-border">

          {/* Logo + collapse button */}
          <div className="px-4 pt-5 pb-4 border-b border-border flex-shrink-0 flex items-start justify-between">
            <div>
              <div className="text-accent font-bold text-base">PortfolioIQ</div>
              <div className="text-text-secondary text-[11px] mt-0.5">Risk Analyzer</div>
            </div>
            <button
              onClick={() => setCollapsed(true)}
              className="p-1 rounded-card text-text-secondary hover:text-text-primary hover:bg-surface transition-colors mt-0.5"
            >
              <ChevronLeft size={15} />
            </button>
          </div>

          {/* Scrollable middle section */}
          <div className="flex-1 overflow-y-auto">

            {/* Navigation */}
            <div className="px-3 py-3">
              <div className="text-text-secondary text-[10px] uppercase tracking-widest mb-2 px-2">
                Navigation
              </div>
              {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => dispatch({ type: 'SET_ACTIVE_NAV', payload: id })}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-card text-sm transition-colors mb-1 ${
                    activeNav === id
                      ? 'bg-surface text-text-primary border-l-2 border-accent'
                      : 'text-text-secondary hover:bg-surface hover:text-text-primary'
                  }`}
                >
                  <Icon size={15} />
                  {label}
                </button>
              ))}
            </div>

            <div className="border-t border-border mx-3" />

            {/* Portfolio inputs */}
            <div className="px-3 py-3">
              <div className="text-text-secondary text-[10px] uppercase tracking-widest mb-3 px-2">
                Portfolio
              </div>

              <div className="flex flex-col gap-2">
                <input
                  value={ticker}
                  onChange={e => setTicker(e.target.value.toUpperCase())}
                  placeholder="e.g. AAPL"
                  className="bg-background border border-border text-text-primary rounded-card px-3 py-2 text-sm w-full focus:border-accent focus:outline-none transition-colors"
                />
                <input
                  type="number"
                  value={quantity}
                  onChange={e => setQuantity(e.target.value)}
                  placeholder="Quantity"
                  className="bg-background border border-border text-text-primary rounded-card px-3 py-2 text-sm w-full focus:border-accent focus:outline-none transition-colors"
                />
                <input
                  type="number"
                  value={buyPrice}
                  onChange={e => setBuyPrice(e.target.value)}
                  placeholder="Buy Price"
                  className="bg-background border border-border text-text-primary rounded-card px-3 py-2 text-sm w-full focus:border-accent focus:outline-none transition-colors"
                />
                <button
                  onClick={addStock}
                  className="bg-surface border border-border text-text-primary hover:border-accent hover:text-accent rounded-card w-full py-2 text-sm transition-colors mt-1"
                >
                  + Add Stock
                </button>
              </div>

              {/* Holdings list */}
              {portfolio.length > 0 && (
                <div className="mt-3">
                  {portfolio.map((h, i) => (
                    <div
                      key={i}
                      className="flex justify-between items-center py-2 border-b border-border last:border-0"
                    >
                      <div>
                        <div className="text-text-primary text-xs font-semibold">{h.ticker}</div>
                        <div className="text-text-secondary text-[10px] mt-0.5">
                          {h.quantity} shares · ₹{h.buy_price}
                        </div>
                      </div>
                      <button
                        onClick={() => removeHolding(i)}
                        className="text-text-secondary hover:text-loss hover:bg-loss/10 p-1 rounded transition-colors flex-shrink-0 ml-2"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Analyse button — sticky bottom, never scrolled away */}
          <div className="p-3 border-t border-border flex-shrink-0">
            <button
              onClick={onAnalyse}
              disabled={portfolio.length === 0 || isLoading}
              className="bg-accent hover:bg-accent/90 text-white rounded-card w-full py-2.5 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Analysing...' : 'Analyse Portfolio'}
            </button>
          </div>

        </div>
      )}

    </div>
  )
}
