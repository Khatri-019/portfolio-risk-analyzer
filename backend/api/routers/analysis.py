"""HTTP routing for analysis endpoints — request parsing and response returning only."""

from fastapi import APIRouter, Depends

from api.controllers import analysis_controller
from api.dependencies import get_groq_api_key, get_news_api_key
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

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/correlation", response_model=CorrelationResponse)
async def correlation_endpoint(request: PortfolioRequest) -> CorrelationResponse:
    """Compute pairwise correlation matrix and diversification score."""
    return await analysis_controller.correlation(request)


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_endpoint(request: PortfolioRequest) -> SimulationResponse:
    """Run Monte Carlo simulation and return projected value distribution."""
    return await analysis_controller.simulate(request)


@router.post("/rebalance", response_model=RebalanceResponse)
async def rebalance_endpoint(request: RebalanceRequest) -> RebalanceResponse:
    """Compute buy/sell trades needed to reach target allocation weights."""
    return await analysis_controller.rebalance(request)


@router.post("/health-report", response_model=HealthReportResponse)
async def health_report_endpoint(
    request: HealthReportRequest,
    groq_api_key: str = Depends(get_groq_api_key),
) -> HealthReportResponse:
    """Generate an AI-powered portfolio health report via Groq."""
    return await analysis_controller.health_report(request, groq_api_key)


@router.post("/sentiment", response_model=SentimentResponse)
async def sentiment_endpoint(
    request: SentimentRequest,
    news_api_key: str = Depends(get_news_api_key),
) -> SentimentResponse:
    """Analyse news sentiment for each portfolio holding using FinBERT."""
    return await analysis_controller.sentiment(request, news_api_key)
