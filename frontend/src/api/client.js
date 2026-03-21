import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const analysePortfolio = (portfolio) =>
  api.post('/portfolio/analyse', { portfolio }).then(r => r.data)

export const fetchBenchmark = (portfolio, benchmark_ticker) =>
  api.post('/portfolio/benchmark', { portfolio, benchmark_ticker }).then(r => r.data)

export const fetchCorrelation = (portfolio) =>
  api.post('/analysis/correlation', { portfolio }).then(r => r.data)

export const fetchSimulation = (portfolio) =>
  api.post('/analysis/simulate', { portfolio }).then(r => r.data)

export const fetchRebalance = (portfolio, target_weights) =>
  api.post('/analysis/rebalance', { portfolio, target_weights }).then(r => r.data)

export const fetchHealthReport = (payload) =>
  api.post('/analysis/health-report', payload).then(r => r.data)

export const fetchSentiment = (tickers_and_names) =>
  api.post('/analysis/sentiment', { tickers_and_names }).then(r => r.data)

export const fetchBenchmarkOptions = () =>
  api.get('/system/benchmarks').then(r => r.data)
