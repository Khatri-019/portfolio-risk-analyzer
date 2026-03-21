"""HTTP routing for system endpoints — request parsing and response returning only."""

from fastapi import APIRouter

from api.controllers import system_controller
from api.models.responses import BenchmarkOptionsResponse, SystemHealthResponse

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=SystemHealthResponse)
async def health_endpoint() -> SystemHealthResponse:
    """Return API liveness status and version."""
    return await system_controller.health()


@router.get("/benchmarks", response_model=BenchmarkOptionsResponse)
async def benchmarks_endpoint() -> BenchmarkOptionsResponse:
    """Return the list of supported benchmark tickers."""
    return await system_controller.benchmarks()
