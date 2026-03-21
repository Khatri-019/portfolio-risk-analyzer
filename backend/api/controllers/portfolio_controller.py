"""Business logic orchestration for portfolio fetch and benchmark endpoints."""

import math

import numpy as np
from fastapi import HTTPException

from api.models.requests import BenchmarkRequest, PortfolioRequest
from api.models.responses import AnalyticsResponse, BenchmarkResponse
from src.portfolio_analytics import compute_analytics, compute_benchmark_comparison, compute_portfolio_history
from src.portfolio_fetcher import fetch_portfolio

_STRIP_KEYS = {"historical_prices", "daily_returns"}


def _serialise_stock(data: dict) -> dict:
    """Strip non-serialisable Series fields and cast numpy scalars to Python natives."""
    result = {}
    for k, v in data.items():
        if k in _STRIP_KEYS:
            continue
        if isinstance(v, np.floating):
            result[k] = float(v)
        elif isinstance(v, np.integer):
            result[k] = int(v)
        else:
            result[k] = v
    return result


async def analyse(request: PortfolioRequest) -> AnalyticsResponse:
    """Fetch live prices and compute per-stock and portfolio-level analytics."""
    portfolio_list = [entry.model_dump() for entry in request.portfolio]
    try:
        portfolio_data, skipped_tickers = fetch_portfolio(portfolio_list)
        if not portfolio_data:
            raise HTTPException(
                status_code=400,
                detail="No valid tickers — all were skipped",
            )
        analytics = compute_analytics(portfolio_data)
        serialised_stocks = {
            ticker: _serialise_stock(data)
            for ticker, data in analytics["stocks"].items()
        }
        return AnalyticsResponse(
            stocks=serialised_stocks,
            portfolio_summary=analytics["portfolio_summary"],
            skipped_tickers=skipped_tickers,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def benchmark(request: BenchmarkRequest) -> BenchmarkResponse:
    """Normalise portfolio vs benchmark to base-100 and compute beta."""
    portfolio_list = [entry.model_dump() for entry in request.portfolio]
    try:
        portfolio_data, _ = fetch_portfolio(portfolio_list)
        if not portfolio_data:
            raise HTTPException(
                status_code=400,
                detail="No valid tickers — all were skipped",
            )
        portfolio_history = compute_portfolio_history(portfolio_data)
        comparison_df, raw_beta = compute_benchmark_comparison(
            portfolio_history, request.benchmark_ticker
        )

        # Fix 2: serialise DatetimeIndex to ISO date strings before converting to records
        if not comparison_df.empty:
            comparison_df.index = comparison_df.index.strftime("%Y-%m-%d")
            records = comparison_df.reset_index().to_dict(orient="records")
        else:
            records = []

        # Fix 4: JSON does not support NaN — map to None
        beta = None if (raw_beta is None or math.isnan(raw_beta)) else float(raw_beta)

        return BenchmarkResponse(comparison=records, beta=beta)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
