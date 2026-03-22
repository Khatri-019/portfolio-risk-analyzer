# PortfolioIQ — Portfolio Risk Analyzer

A full-stack financial dashboard for analyzing portfolio performance, 
risk metrics, and AI-driven insights. Built with FastAPI, React, 
FinBERT sentiment analysis, and Monte Carlo simulation.

## Live Features

- **Real-time market data** via Yahoo Finance API
- **Risk metrics** — Sharpe Ratio, Beta, Max Drawdown, Volatility
- **Monte Carlo Simulation** — 1,000 path projection over 252 trading days
- **Benchmark Comparison** — Portfolio vs S&P 500, NASDAQ, Nifty 50
- **Correlation Analysis** — Heatmap + Diversification Score
- **Portfolio Rebalancer** — Target allocation with trade instructions
- **AI Health Report** — LLaMA 3.3 (via Groq) portfolio analysis
- **News Sentiment** — FinBERT NLP classification on live headlines

## Tech Stack

### Backend
- **FastAPI** — layered backend architecture (routers → controllers → services)
- **Python** — pandas, numpy, yfinance
- **Groq API** — LLaMA 3.3 70B for AI health reports
- **FinBERT** — HuggingFace transformer for financial sentiment
- **NewsAPI** — Live news headlines per ticker

### Frontend
- **React + Vite** — Modern frontend tooling
- **Tailwind CSS** — Dark fintech design system
- **Recharts** — Interactive financial charts
- **React Query** — Server state management

## Project Structure
```
portfolio-risk-analyzer/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── api/
│   │   ├── controllers/           # Business logic layer
│   │   ├── routers/               # Route definitions
│   │   └── models/                # Pydantic request/response models
│   └── src/
│       ├── portfolio_fetcher.py   # Yahoo Finance data fetching
│       ├── portfolio_analytics.py # Metrics computation
│       ├── correlation.py         # Correlation matrix + diversification
│       ├── simulation.py          # Monte Carlo simulation
│       ├── rebalancer.py          # Rebalancing trade computation
│       ├── ai_analyst.py          # Groq LLM health report
│       └── sentiment.py           # FinBERT news sentiment
└── frontend/
    └── src/
        ├── pages/                 # 6 dashboard pages
        ├── components/            # Reusable UI components
        ├── api/                   # API client
        ├── hooks/                 # React Query hooks
        └── store/                 # Global state (Context + useReducer)
```

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Conda (recommended)
- Groq API key (free at console.groq.com)
- NewsAPI key (free at newsapi.org)

### Backend
```bash
cd backend
conda create -n portfolio-analyzer python=3.10
conda activate portfolio-analyzer
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env
echo "NEWS_API_KEY=your_key_here" >> .env

# Start server
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/portfolio/analyse` | Full portfolio analytics |
| POST | `/api/portfolio/benchmark` | Benchmark comparison |
| POST | `/api/analysis/correlation` | Correlation matrix |
| POST | `/api/analysis/simulate` | Monte Carlo simulation |
| POST | `/api/analysis/rebalance` | Rebalancing trades |
| POST | `/api/analysis/health-report` | AI health report |
| POST | `/api/analysis/sentiment` | News sentiment |
| GET | `/api/system/health` | Health check |

## Key Metrics

| Metric | Formula |
|--------|---------|
| Sharpe Ratio | `(mean_return / std_return) × √252` |
| Volatility | `std(daily_returns) × √252` |
| Max Drawdown | `(peak - trough) / peak × 100` |
| Beta | `cov(portfolio, benchmark) / var(benchmark)` |
| VaR 95% | `current_value - percentile(simulated_values, 5)` |

## Notes

- FinBERT first load downloads ~500MB model weights (cached after first run)
- News sentiment uses NewsAPI free tier (100 req/day limit)
- Yahoo Finance rate limiting may affect data fetching on restricted networks
- All prices are in USD

## License

MIT License