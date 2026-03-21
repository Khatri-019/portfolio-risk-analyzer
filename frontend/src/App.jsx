import { useEffect, useRef } from 'react'
import { PortfolioProvider, usePortfolioStore } from './store/portfolioStore'
import { useAnalytics } from './hooks/usePortfolio'
import Layout from './components/layout/Layout'
import OverviewPage from './pages/OverviewPage'
import HoldingsPage from './pages/HoldingsPage'
import RiskPage from './pages/RiskPage'
import SimulationPage from './pages/SimulationPage'


const PAGE_NAMES = {
  overview:   'Overview',
  holdings:   'Holdings',
  risk:       'Risk & Correlation',
  simulation: 'Simulation',
  rebalancer: 'Rebalancer',
  insights:   'AI Insights',
}

function AppInner() {
  const { state } = usePortfolioStore()
  const { mutate: runAnalysis, data: analytics, isLoading, isError, error } = useAnalytics()
  const portfolio = state.portfolio

  const hasFetched = useRef(false)
  useEffect(() => {
    if (!hasFetched.current) {
      hasFetched.current = true
      runAnalysis(portfolio)
    }
  }, [])

  let page
  switch (state.activeNav) {
    case 'overview':
      page = (
        <OverviewPage
          analytics={analytics}
          onAnalyse={() => runAnalysis(portfolio)}
          isLoading={isLoading}
          isError={isError}
          error={error}
        />
      )
      break
    case 'holdings':
      page = <HoldingsPage analyticsData={analytics} />
      break
    case 'risk':
      page = <RiskPage portfolio={portfolio} analyticsData={analytics} />
      break
    case 'simulation':
      page = <SimulationPage portfolio={portfolio} />
      break
    default:
      page = (
        <div className="text-text-secondary text-sm p-4">
          {PAGE_NAMES[state.activeNav] ?? 'Overview'} — coming soon
        </div>
      )
  }

  return (
    <Layout analytics={analytics} onAnalyse={() => runAnalysis(portfolio)} isLoading={isLoading}>
      {page}
    </Layout>
  )
}

export default function App() {
  return (
    <PortfolioProvider>
      <AppInner />
    </PortfolioProvider>
  )
}
