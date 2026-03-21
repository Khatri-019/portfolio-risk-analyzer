"""Business logic orchestration for correlation, simulation, rebalance, AI report, and sentiment endpoints."""

from fastapi import HTTPException

from api.models.requests import (
    HealthReportRequest,
    PortfolioRequest,
    RebalanceRequest,
    SentimentRequest,
)
from api.models.responses import (
    CorrelationResponse,
    HealthReportResponse,
    RebalanceResponse,
    SentimentResponse,
    SimulationResponse,
)
from src.ai_analyst import generate_portfolio_health_report
from src.correlation import compute_correlation_matrix, compute_diversification_score
from src.portfolio_analytics import compute_analytics, compute_portfolio_history
from src.portfolio_fetcher import fetch_portfolio
from src.rebalancer import compute_rebalance_trades
from src.sentiment import analyse_portfolio_sentiment
from src.simulation import get_simulation_summary, run_monte_carlo

_HEALTH_REPORT_KEYS = {"health_score", "health_label", "summary", "risk_factors", "suggestions"}


async def correlation(request: PortfolioRequest) -> CorrelationResponse:
    """Compute pairwise return correlation matrix and portfolio diversification score."""
    portfolio_list = [entry.model_dump() for entry in request.portfolio]
    try:
        portfolio_data, _ = fetch_portfolio(portfolio_list)
        if not portfolio_data:
            raise HTTPException(status_code=400, detail="No valid tickers — all were skipped")
        analytics = compute_analytics(portfolio_data)
        matrix = compute_correlation_matrix(analytics["stocks"])
        div_score = compute_diversification_score(matrix, analytics["stocks"])

        # Cast nested np.float64 values — Pydantic won't coerce them inside an untyped dict
        serialised_matrix = {
            row: {col: float(val) for col, val in row_data.items()}
            for row, row_data in matrix.to_dict().items()
        }
        return CorrelationResponse(
            correlation_matrix=serialised_matrix,
            diversification=div_score,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def simulate(request: PortfolioRequest) -> SimulationResponse:
    """Run Monte Carlo simulation and return projected value distribution with 50 sample paths."""
    portfolio_list = [entry.model_dump() for entry in request.portfolio]
    try:
        portfolio_data, _ = fetch_portfolio(portfolio_list)
        if not portfolio_data:
            raise HTTPException(status_code=400, detail="No valid tickers — all were skipped")
        portfolio_history = compute_portfolio_history(portfolio_data)
        simulation_result = run_monte_carlo(portfolio_history)
        summary = get_simulation_summary(simulation_result)

        # paths shape: (n_days+1, n_simulations) — send first 50 columns only to cap payload size
        paths_sample = simulation_result["paths"][:, :50].tolist()

        return SimulationResponse(
            summary=summary,
            percentiles={
                "p10": simulation_result["p10"],
                "p50": simulation_result["p50"],
                "p90": simulation_result["p90"],
                "current_value": simulation_result["current_value"],
            },
            paths_sample=paths_sample,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def rebalance(request: RebalanceRequest) -> RebalanceResponse:
    """Compute buy/sell trades required to reach the caller-supplied target weights."""
    portfolio_list = [entry.model_dump() for entry in request.portfolio]
    try:
        portfolio_data, _ = fetch_portfolio(portfolio_list)
        if not portfolio_data:
            raise HTTPException(status_code=400, detail="No valid tickers — all were skipped")
        analytics = compute_analytics(portfolio_data)
        result = compute_rebalance_trades(analytics["stocks"], request.target_weights)
        return RebalanceResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def health_report(
    request: HealthReportRequest,
    groq_api_key: str,
) -> HealthReportResponse:
    """Generate an AI portfolio health report via Groq; never raises on API failure."""
    try:
        report = generate_portfolio_health_report(
            request.portfolio_summary,
            request.diversification,
            request.simulation_summary,
            groq_api_key,
        )
        # Fix 1: generate_portfolio_health_report may return an extra "error" key on failure;
        # filter to the known schema keys so Pydantic unpacking does not raise.
        clean_report = {k: v for k, v in report.items() if k in _HEALTH_REPORT_KEYS}
        return HealthReportResponse(**clean_report)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def sentiment(
    request: SentimentRequest,
    news_api_key: str,
) -> SentimentResponse:
    """Run FinBERT news sentiment analysis across all holdings in the request."""
    try:
        result = analyse_portfolio_sentiment(request.tickers_and_names, news_api_key)
        return SentimentResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
