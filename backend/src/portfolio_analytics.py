"""Metric computation for a stock portfolio — consumes fetcher output, no data re-fetching."""

import logging
import math
    

import pandas as pd
import requests

from src.portfolio_fetcher import MIN_HISTORY_DAYS

logger = logging.getLogger(__name__)

TRADING_DAYS = 252


def compute_portfolio_history(portfolio_data: dict) -> pd.Series:
    """Return total portfolio value per trading day as a single aligned Series.

    Each ticker's historical_prices is multiplied by its quantity before alignment.
    All per-ticker value series are aligned on a common DatetimeIndex via concat
    and summed column-wise so every date reflects the full portfolio value.
    """
    if not portfolio_data:
        raise ValueError(
            "portfolio_data is empty — no tickers were successfully fetched."
        )

    value_series: list[pd.Series] = []
    for ticker, data in portfolio_data.items():
        ticker_value: pd.Series = data["historical_prices"] * data["quantity"]
        ticker_value.name = ticker
        value_series.append(ticker_value)

    combined: pd.DataFrame = pd.concat(value_series, axis=1)
    portfolio_history: pd.Series = combined.sum(axis=1)
    portfolio_history.name = "portfolio_value"
    return portfolio_history


def _compute_stock_metrics(ticker: str, data: dict) -> dict:
    """Compute per-stock analytics and return the extended ticker dict.

    Adds pct_return, daily_returns, volatility, sharpe_ratio, and max_drawdown
    to a copy of the input dict.  volatility, sharpe_ratio, and max_drawdown are
    set to None when history is shorter than MIN_HISTORY_DAYS trading days.
    """
    result = dict(data)

    result["pct_return"] = (data["gain_loss"] / data["investment_value"]) * 100

    daily_returns: pd.Series = data["historical_prices"].pct_change().dropna()
    result["daily_returns"] = daily_returns

    if len(daily_returns) < MIN_HISTORY_DAYS:
        logger.warning(
            "Ticker '%s' has only %d days of return history (minimum %d). "
            "volatility, sharpe_ratio, and max_drawdown set to None.",
            ticker,
            len(daily_returns),
            MIN_HISTORY_DAYS,
        )
        result["volatility"] = None
        result["sharpe_ratio"] = None
        result["max_drawdown"] = None
        return result

    std = daily_returns.std()
    sqrt_days = math.sqrt(TRADING_DAYS)

    result["volatility"] = std * sqrt_days
    result["sharpe_ratio"] = (daily_returns.mean() / std) * sqrt_days

    cumulative: pd.Series = (1 + daily_returns).cumprod()
    result["max_drawdown"] = (cumulative / cumulative.cummax() - 1).min() * 100

    return result


def compute_analytics(portfolio_data: dict) -> dict:
    """Compute all per-stock and portfolio-level metrics from fetched portfolio data.

    Accepts the dict returned by fetch_portfolio() and returns a structured result
    with 'stocks' (per-ticker extended dicts) and 'portfolio_summary'.
    No side effects — does not fetch data or modify the input.
    """
    stocks: dict = {}
    for ticker, data in portfolio_data.items():
        stocks[ticker] = _compute_stock_metrics(ticker, data)

    portfolio_history: pd.Series = compute_portfolio_history(portfolio_data)

    total_investment: float = sum(d["investment_value"] for d in portfolio_data.values())
    total_current_value: float = sum(d["current_value"] for d in portfolio_data.values())
    total_gain_loss: float = total_current_value - total_investment
    overall_pct_return: float = (total_gain_loss / total_investment) * 100

    portfolio_daily_returns: pd.Series = portfolio_history.pct_change().dropna()
    port_std = portfolio_daily_returns.std()
    sqrt_days = math.sqrt(TRADING_DAYS)

    port_cumulative: pd.Series = (1 + portfolio_daily_returns).cumprod()
    portfolio_max_drawdown: float = (
        (port_cumulative / port_cumulative.cummax() - 1).min() * 100
    )

    portfolio_summary: dict = {
        "total_investment": total_investment,
        "total_current_value": total_current_value,
        "total_gain_loss": total_gain_loss,
        "overall_pct_return": overall_pct_return,
        "portfolio_volatility": port_std * sqrt_days,
        "portfolio_sharpe": (portfolio_daily_returns.mean() / port_std) * sqrt_days,
        "portfolio_max_drawdown": portfolio_max_drawdown,
        "beta": None,
    }

    return {"stocks": stocks, "portfolio_summary": portfolio_summary}


def compute_benchmark_comparison(
    portfolio_history: pd.Series,
    benchmark_ticker: str,
) -> tuple[pd.DataFrame, float]:
    """Fetch benchmark data and return a normalised comparison DataFrame plus beta.

    Steps:
    1. Fetch benchmark Close prices for the same date range as portfolio_history.
    2. Align both series on common trading dates (inner join on date index).
    3. Forward-fill benchmark gaps of up to 2 days to handle exchange holidays,
       then drop any remaining NaNs.
    4. Rebase both series to 100 at the first common date.
    5. Compute beta = cov(portfolio_returns, benchmark_returns) / var(benchmark_returns)
       using simple daily returns on the aligned raw series.

    Returns a tuple of (comparison_df, beta) where comparison_df has columns
    'portfolio_normalised' and 'benchmark_normalised' with a DatetimeIndex.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{benchmark_ticker}"
    params = {
        "period1": int(portfolio_history.index.min().timestamp()),
        "period2": int(portfolio_history.index.max().timestamp()),
        "interval": "1d",
        "events": "history",
    }

    response = session.get(url, params=params, timeout=15)
    data = response.json()

    result = data.get("chart", {}).get("result")
    if not result:
        logger.warning(
            "No benchmark data returned for '%s'. Benchmark comparison unavailable.",
            benchmark_ticker,
        )
        empty_df = pd.DataFrame(columns=["portfolio_normalised", "benchmark_normalised"])
        return empty_df, float("nan")

    chart = result[0]
    timestamps = chart.get("timestamp", [])
    closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])

    if not timestamps or not closes:
        logger.warning(
            "No benchmark data returned for '%s'. Benchmark comparison unavailable.",
            benchmark_ticker,
        )
        empty_df = pd.DataFrame(columns=["portfolio_normalised", "benchmark_normalised"])
        return empty_df, float("nan")

    dates = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert("Asia/Kolkata").normalize()
    benchmark_prices: pd.Series = pd.Series(
        [float(c) if c is not None else None for c in closes],
        index=dates,
        name=benchmark_ticker,
    ).dropna()

    # Normalise both indexes to timezone-naive dates for alignment
    portfolio_index = portfolio_history.index.normalize().tz_localize(None)
    benchmark_index = benchmark_prices.index.normalize().tz_localize(None)

    portfolio_aligned = pd.Series(
        portfolio_history.values, index=portfolio_index, name="portfolio"
    )
    benchmark_aligned = pd.Series(
        benchmark_prices.values, index=benchmark_index, name="benchmark"
    )

    combined: pd.DataFrame = pd.concat(
        [portfolio_aligned, benchmark_aligned], axis=1, join="inner"
    )

    combined["benchmark"] = combined["benchmark"].ffill(limit=2)
    combined = combined.dropna()

    if combined.empty:
        logger.warning(
            "No overlapping dates between portfolio and benchmark '%s'.",
            benchmark_ticker,
        )
        empty_df = pd.DataFrame(columns=["portfolio_normalised", "benchmark_normalised"])
        return empty_df, float("nan")

    port_raw: pd.Series = combined["portfolio"]
    bench_raw: pd.Series = combined["benchmark"]

    comparison_df = pd.DataFrame(
        {
            "portfolio_normalised": port_raw / port_raw.iloc[0] * 100,
            "benchmark_normalised": bench_raw / bench_raw.iloc[0] * 100,
        }
    )

    port_returns: pd.Series = port_raw.pct_change().dropna()
    bench_returns: pd.Series = bench_raw.pct_change().dropna()

    covariance = port_returns.cov(bench_returns)
    bench_variance = bench_returns.var()
    beta: float = covariance / bench_variance if bench_variance != 0 else float("nan")

    return comparison_df, beta
