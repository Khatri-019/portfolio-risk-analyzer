"""Static responses for liveness and configuration endpoints."""

from api.models.responses import BenchmarkOptionsResponse, SystemHealthResponse

_BENCHMARK_OPTIONS = [
    {"label": "Nifty 50", "ticker": "^NSEI"},
    {"label": "S&P 500", "ticker": "^GSPC"},
    {"label": "NASDAQ", "ticker": "^IXIC"},
]


async def health() -> SystemHealthResponse:
    """Return API liveness status and current version."""
    return SystemHealthResponse(status="ok", version="1.0.0")


async def benchmarks() -> BenchmarkOptionsResponse:
    """Return the supported benchmark index options for frontend dropdowns."""
    return BenchmarkOptionsResponse(benchmarks=_BENCHMARK_OPTIONS)
