"""Pydantic request models for all API endpoints."""

from pydantic import BaseModel


class PortfolioEntry(BaseModel):
    ticker: str
    quantity: int
    buy_price: float


class PortfolioRequest(BaseModel):
    portfolio: list[PortfolioEntry]


class BenchmarkRequest(BaseModel):
    portfolio: list[PortfolioEntry]
    benchmark_ticker: str


class RebalanceRequest(BaseModel):
    portfolio: list[PortfolioEntry]
    target_weights: dict[str, float]


class SentimentRequest(BaseModel):
    tickers_and_names: dict[str, str]


class HealthReportRequest(BaseModel):
    portfolio_summary: dict
    diversification: dict
    simulation_summary: dict
