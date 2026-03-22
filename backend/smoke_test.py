import sys
sys.path.insert(0, '.')
from src.portfolio_fetcher import fetch_portfolio
from src.portfolio_analytics import compute_portfolio_history

data, skipped = fetch_portfolio([
    {"ticker": "AAPL", "quantity": 10, "buy_price": 150.0},
    {"ticker": "MSFT", "quantity": 8,  "buy_price": 280.0},
    {"ticker": "NVDA", "quantity": 4,  "buy_price": 450.0},
])

history = compute_portfolio_history(data)
print("Length:", len(history))
print("Min:", history.min())
print("Max:", history.max())
print("Last:", history.iloc[-1])
print("First 5 values:")
print(history.head())
print("Last 5 values:")
print(history.tail())
