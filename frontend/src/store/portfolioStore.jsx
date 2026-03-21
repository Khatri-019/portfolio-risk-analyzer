import { createContext, useContext, useReducer } from 'react'

// Client-side UI state only.
// Server state (analytics, simulation, etc.)
// lives in React Query — never here.
const initialState = {
  portfolio: [
    { ticker: 'AAPL',  quantity: 10, buy_price: 150.0 },
    { ticker: 'MSFT',  quantity: 8,  buy_price: 280.0 },
    { ticker: 'GOOGL', quantity: 5,  buy_price: 140.0 },
    { ticker: 'AMZN',  quantity: 6,  buy_price: 178.0 },
    { ticker: 'TSLA',  quantity: 7,  buy_price: 200.0 },
    { ticker: 'NVDA',  quantity: 4,  buy_price: 450.0 },
    { ticker: 'META',  quantity: 5,  buy_price: 320.0 },
    { ticker: 'JPM',   quantity: 8,  buy_price: 195.0 },
    { ticker: 'GS',    quantity: 3,  buy_price: 380.0 },
    { ticker: 'MS',    quantity: 6,  buy_price: 88.0  },
    { ticker: 'NFLX',  quantity: 4,  buy_price: 550.0 },
    { ticker: 'AMD',   quantity: 9,  buy_price: 120.0 },
  ],
  activeNav: 'overview',
  selectedBenchmark: '^GSPC',
}

function reducer(state, action) {
  switch (action.type) {
    case 'ADD_HOLDING':
      return { ...state, portfolio: [...state.portfolio, action.payload] }
    case 'REMOVE_HOLDING':
      return {
        ...state,
        portfolio: state.portfolio.filter((_, i) => i !== action.payload),
      }
    case 'SET_PORTFOLIO':
      return { ...state, portfolio: action.payload }
    case 'SET_ACTIVE_NAV':
      return { ...state, activeNav: action.payload }
    case 'SET_BENCHMARK':
      return { ...state, selectedBenchmark: action.payload }
    default:
      return state
  }
}

const PortfolioContext = createContext(null)

export function PortfolioProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return (
    <PortfolioContext.Provider value={{ state, dispatch }}>
      {children}
    </PortfolioContext.Provider>
  )
}

export function usePortfolioStore() {
  const ctx = useContext(PortfolioContext)
  if (!ctx) throw new Error('usePortfolioStore must be used within PortfolioProvider')
  return ctx
}
