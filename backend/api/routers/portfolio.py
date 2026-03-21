"""HTTP routing for portfolio endpoints — request parsing and response returning only."""

from fastapi import APIRouter

from api.controllers import portfolio_controller
from api.models.requests import BenchmarkRequest, PortfolioRequest
from api.models.responses import AnalyticsResponse, BenchmarkResponse

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/analyse", response_model=AnalyticsResponse)
async def analyse_endpoint(request: PortfolioRequest) -> AnalyticsResponse:
    """Fetch live prices and compute full portfolio analytics."""
    return await portfolio_controller.analyse(request)


@router.post("/benchmark", response_model=BenchmarkResponse)
async def benchmark_endpoint(request: BenchmarkRequest) -> BenchmarkResponse:
    """Compare portfolio performance against a market benchmark."""
    return await portfolio_controller.benchmark(request)
