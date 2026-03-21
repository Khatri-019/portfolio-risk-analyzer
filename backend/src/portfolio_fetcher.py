"""Input validation and direct Yahoo Finance API data retrieval for portfolio holdings."""
# run from project root: python -m src.portfolio_fetcher

import logging
from datetime import datetime, timedelta

import pandas as pd
import requests

logger = logging.getLogger(__name__)

HISTORY_PERIOD = "1y"
MIN_HISTORY_DAYS = 30

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
_QUOTE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d"


def _create_session() -> requests.Session:
    """Create a browser-like requests session for Yahoo Finance API calls."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    return session


def validate_input(portfolio: list[dict]) -> None:
    """Validate every entry in the portfolio list; raise ValueError listing all violations."""
    errors: list[str] = []

    for i, entry in enumerate(portfolio):
        ticker = entry.get("ticker")
        quantity = entry.get("quantity")
        buy_price = entry.get("buy_price")

        label = f"Entry {i}" if not isinstance(ticker, str) or not ticker.strip() else f"Entry {i} ({ticker})"

        if not isinstance(ticker, str) or not ticker.strip():
            errors.append(f"{label}: 'ticker' must be a non-empty string, got {ticker!r}.")

        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            errors.append(f"{label}: 'quantity' must be a positive integer, got {quantity!r}.")

        if not isinstance(buy_price, (int, float)) or isinstance(buy_price, bool) or buy_price <= 0:
            errors.append(f"{label}: 'buy_price' must be a positive number, got {buy_price!r}.")

    if errors:
        raise ValueError("Portfolio validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


def fetch_ticker_data(ticker: str, quantity: int, buy_price: float, session: requests.Session) -> dict | None:
    """Fetch current price and 1-year history for a single ticker via Yahoo Finance API.

    Returns a structured dict of price and value fields, or None if no data is found.
    """
    try:
        # Calculate 1Y date range as unix timestamps
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())

        url = _CHART_URL.format(ticker=ticker)
        params = {
            "period1": start_ts,
            "period2": end_ts,
            "interval": "1d",
            "events": "history",
        }

        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        result = data.get("chart", {}).get("result")
        if not result:
            logger.warning(f"No data found for ticker '{ticker}'. Skipping.")
            return None

        chart = result[0]
        timestamps = chart.get("timestamp", [])
        closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])

        if not timestamps or not closes:
            logger.warning(f"No data found for ticker '{ticker}'. Skipping.")
            return None

        # Build historical prices as pd.Series with DatetimeIndex
        dates = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert("Asia/Kolkata").normalize()
        historical_prices = pd.Series(
           [float(c) if c is not None else None for c in closes],
            index=dates,
            name=ticker
        ).dropna()

        if len(historical_prices) < MIN_HISTORY_DAYS:
            logger.warning(f"Insufficient history for '{ticker}'. Skipping.")
            return None

        # Current price from meta field — most reliable, no extra call needed
        current_price: float = float(
            chart.get("meta", {}).get("regularMarketPrice")
            or historical_prices.iloc[-1]
        )

        investment_value = quantity * float(buy_price)
        current_value = quantity * current_price
        gain_loss = current_value - investment_value

        return {
            "current_price": current_price,
            "quantity": quantity,
            "buy_price": float(buy_price),
            "historical_prices": historical_prices,
            "investment_value": investment_value,
            "current_value": current_value,
            "gain_loss": gain_loss,
        }

    except Exception as e:
        logger.warning(f"Failed to fetch data for '{ticker}': {e}. Skipping.")
        return None


def fetch_portfolio(portfolio: list[dict]) -> tuple[dict, list[str]]:
    """Validate and fetch data for all tickers in the portfolio.

    Returns a tuple of (portfolio_data, skipped_tickers) where skipped_tickers
    lists any tickers for which the API returned no data.
    """
    validate_input(portfolio)

    session = _create_session()
    portfolio_data: dict = {}
    skipped_tickers: list[str] = []

    for entry in portfolio:
        ticker: str = entry["ticker"].strip().upper()
        quantity: int = entry["quantity"]
        buy_price: float = entry["buy_price"]

        result = fetch_ticker_data(ticker, quantity, buy_price, session)
        if result is None:
            skipped_tickers.append(ticker)
        else:
            portfolio_data[ticker] = result

    return portfolio_data, skipped_tickers


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)