import { useState, useMemo } from 'react'
import { Briefcase } from 'lucide-react'
import clsx from 'clsx'
import Card from '../components/ui/Card'
import {
  formatCurrency,
  formatPct,
  getProfitClass,
} from '../utils/formatters'

const COLUMNS = [
  { key: 'ticker',           label: 'Ticker',        sortable: false },
  { key: 'quantity',         label: 'Qty',           sortable: true  },
  { key: 'buy_price',        label: 'Buy Price',     sortable: true  },
  { key: 'current_price',    label: 'Current Price', sortable: true  },
  { key: 'investment_value', label: 'Invested',      sortable: true  },
  { key: 'current_value',    label: 'Current Value', sortable: true  },
  { key: 'gain_loss',        label: 'Gain / Loss',   sortable: true  },
  { key: 'pct_return',       label: 'Return %',      sortable: true  },
  { key: 'volatility',       label: 'Volatility',    sortable: true  },
  { key: 'sharpe_ratio',     label: 'Sharpe',        sortable: true  },
  { key: 'max_drawdown',     label: 'Max Drawdown',  sortable: true  },
]

// volatility arrives as a decimal (0.267) — multiply by 100 unless already a pct
function fmtVolatility(val) {
  if (val === null || val === undefined) return null
  return formatPct(val < 1 ? val * 100 : val)
}

function SortIcon({ column, sortKey, sortDir }) {
  if (column === sortKey) {
    return (
      <span className="ml-1 text-accent">
        {sortDir === 'asc' ? '↑' : '↓'}
      </span>
    )
  }
  return (
    <span className="ml-1 text-text-secondary opacity-0 group-hover:opacity-40 transition-opacity">
      ↕
    </span>
  )
}

// Returns a <td> — valid as a direct child of <tr> in React
function Cell({ col, row }) {
  const val = row[col.key]
  const base = 'px-4 py-3 text-sm'
  const right = `${base} text-right`
  const NA = <span className="text-text-secondary">N/A</span>

  switch (col.key) {
    case 'ticker':
      return (
        <td className={`${base} text-left font-semibold text-primary whitespace-nowrap`}>
          {val}
        </td>
      )
    case 'quantity':
      return <td className={`${right} text-primary`}>{val}</td>
    case 'buy_price':
    case 'current_price':
    case 'investment_value':
    case 'current_value':
      return (
        <td className={`${right} text-primary whitespace-nowrap`}>
          {formatCurrency(val)}
        </td>
      )
    case 'gain_loss':
      return (
        <td className={clsx(right, 'font-medium whitespace-nowrap', getProfitClass(val))}>
          {formatCurrency(val)}
        </td>
      )
    case 'pct_return':
      return (
        <td className={clsx(right, 'font-medium', getProfitClass(val))}>
          {val !== null && val !== undefined ? formatPct(val) : NA}
        </td>
      )
    case 'volatility': {
      const formatted = fmtVolatility(val)
      return (
        <td className={`${right} text-primary`}>
          {formatted ?? NA}
        </td>
      )
    }
    case 'sharpe_ratio':
      return (
        <td className={`${right} text-primary`}>
          {val !== null && val !== undefined ? Number(val).toFixed(2) : NA}
        </td>
      )
    case 'max_drawdown':
      return (
        <td className={`${right} text-loss`}>
          {val !== null && val !== undefined ? formatPct(val) : NA}
        </td>
      )
    default:
      return <td className={`${right} text-primary`}>{val}</td>
  }
}

export default function HoldingsPage({ analyticsData }) {
  const [sortKey, setSortKey] = useState('current_value')
  const [sortDir, setSortDir] = useState('desc')

  const rows = useMemo(() => {
    if (!analyticsData) return []
    return Object.entries(analyticsData.stocks).map(([ticker, d]) => ({ ticker, ...d }))
  }, [analyticsData])

  const sortedRows = useMemo(() => {
    return [...rows].sort((a, b) => {
      const aVal = a[sortKey]
      const bVal = b[sortKey]
      if (aVal == null && bVal == null) return 0
      if (aVal == null) return 1
      if (bVal == null) return -1
      return sortDir === 'asc' ? aVal - bVal : bVal - aVal
    })
  }, [rows, sortKey, sortDir])

  function handleSort(key) {
    if (key === sortKey) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  if (!analyticsData) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-text-secondary">
        <Briefcase size={32} className="mb-3 opacity-40" />
        <p className="text-sm">No holdings available.</p>
        <p className="text-xs mt-1 opacity-60">
          Add stocks in the sidebar and click Analyse.
        </p>
      </div>
    )
  }

  const { portfolio_summary } = analyticsData
  const {
    total_investment,
    total_current_value,
    total_gain_loss,
    overall_pct_return,
  } = portfolio_summary

  return (
    <div className="overflow-x-auto">
      <Card className="p-0">
        <div className="px-4 pt-4 pb-2 flex items-baseline gap-2">
          <p className="uppercase text-[10px] tracking-widest text-text-secondary font-medium">
            Holdings
          </p>
          <span className="text-[11px] text-text-secondary">{rows.length} positions</span>
        </div>

        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-background sticky top-0 z-10">
              {COLUMNS.map(col => (
                <th
                  key={col.key}
                  onClick={() => col.sortable && handleSort(col.key)}
                  className={clsx(
                    'text-[11px] uppercase tracking-wider text-text-secondary font-medium px-4 py-3 select-none',
                    col.key === 'ticker'
                      ? 'text-left cursor-default'
                      : 'text-right cursor-pointer hover:text-primary',
                    col.sortable && 'group'
                  )}
                >
                  {col.label}
                  {col.sortable && (
                    <SortIcon column={col.key} sortKey={sortKey} sortDir={sortDir} />
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {sortedRows.map(row => (
              <tr
                key={row.ticker}
                className="border-b border-border hover:bg-border/50 transition-colors"
              >
                {COLUMNS.map(col => (
                  <Cell key={col.key} col={col} row={row} />
                ))}
              </tr>
            ))}
          </tbody>

          <tfoot>
            <tr className="bg-surface/50 border-t-2 border-border font-semibold">
              <td className="px-4 py-3 text-left text-[11px] uppercase text-text-secondary">
                Total
              </td>
              {/* Qty, Buy Price, Current Price — no aggregate */}
              <td className="px-4 py-3 text-right text-primary text-sm">—</td>
              <td className="px-4 py-3 text-right text-primary text-sm">—</td>
              <td className="px-4 py-3 text-right text-primary text-sm">—</td>
              <td className="px-4 py-3 text-right text-primary text-sm whitespace-nowrap">
                {formatCurrency(total_investment)}
              </td>
              <td className="px-4 py-3 text-right text-primary text-sm whitespace-nowrap">
                {formatCurrency(total_current_value)}
              </td>
              <td
                className={clsx(
                  'px-4 py-3 text-right font-medium text-sm whitespace-nowrap',
                  getProfitClass(total_gain_loss)
                )}
              >
                {formatCurrency(total_gain_loss)}
              </td>
              <td
                className={clsx(
                  'px-4 py-3 text-right font-medium text-sm',
                  getProfitClass(overall_pct_return)
                )}
              >
                {formatPct(overall_pct_return)}
              </td>
              {/* Volatility, Sharpe, Max Drawdown — no portfolio-level aggregate per stock */}
              <td className="px-4 py-3 text-right text-primary text-sm">—</td>
              <td className="px-4 py-3 text-right text-primary text-sm">—</td>
              <td className="px-4 py-3 text-right text-primary text-sm">—</td>
            </tr>
          </tfoot>
        </table>
      </Card>
    </div>
  )
}
