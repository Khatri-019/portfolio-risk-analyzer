"""Pydantic response models for all API endpoints."""

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    stocks: dict
    portfolio_summary: dict
    portfolio_history: list[dict]
    skipped_tickers: list[str]


class BenchmarkResponse(BaseModel):
    comparison: list
    beta: float | None


class CorrelationResponse(BaseModel):
    correlation_matrix: dict
    diversification: dict


class SimulationResponse(BaseModel):
    summary: dict
    percentiles: dict
    paths_sample: list


class RebalanceResponse(BaseModel):
    trades: list
    instructions: list[str]
    total_buy_value: float
    total_sell_value: float
    total_portfolio_value: float


class HealthReportResponse(BaseModel):
    health_score: int
    health_label: str
    summary: str
    risk_factors: list
    suggestions: list


class SentimentResponse(BaseModel):
    ticker_sentiments: dict
    portfolio_sentiment: str
    summary: str


class SystemHealthResponse(BaseModel):
    status: str
    version: str


class BenchmarkOptionsResponse(BaseModel):
    benchmarks: list[dict]
