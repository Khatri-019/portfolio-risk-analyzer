import { useMutation, useQuery } from '@tanstack/react-query'
import { analysePortfolio, fetchBenchmarkOptions } from '../api/client'
import { usePortfolioStore } from '../store/portfolioStore'

export function useAnalytics() {
  return useMutation({
    mutationFn: (portfolio) => analysePortfolio(portfolio),
    retry: 1,
  })
}

export function usePortfolioActions() {
  const { dispatch } = usePortfolioStore()
  return {
    addHolding:    (holding)   => dispatch({ type: 'ADD_HOLDING',   payload: holding }),
    removeHolding: (index)     => dispatch({ type: 'REMOVE_HOLDING', payload: index }),
    setPortfolio:  (portfolio) => dispatch({ type: 'SET_PORTFOLIO',  payload: portfolio }),
  }
}

export function useBenchmarkOptions() {
  return useQuery({
    queryKey: ['benchmarkOptions'],
    queryFn: fetchBenchmarkOptions,
    staleTime: Infinity,
  })
}
