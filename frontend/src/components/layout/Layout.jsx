import { usePortfolioStore } from '../../store/portfolioStore'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function Layout({ children, analytics, onAnalyse, isLoading }) {
  const { state } = usePortfolioStore()

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar onAnalyse={onAnalyse} isLoading={isLoading} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <TopBar analytics={analytics} activeNav={state.activeNav} />
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {children}
        </main>
      </div>
    </div>
  )
}
