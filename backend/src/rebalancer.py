"""Portfolio rebalancing trade computation."""

import logging

from src.utils import format_currency

logger = logging.getLogger(__name__)

_ACTION_ORDER = {"SELL": 0, "BUY": 1, "HOLD": 2}


def validate_target_weights(
    target_weights: dict[str, float],
    portfolio_tickers: set[str],
) -> None:
    """Validate user-provided target allocations.

    Collects all violations before raising so the caller sees every problem
    in a single error rather than fixing one at a time.
    """
    violations: list[str] = []

    non_positive = [t for t, w in target_weights.items() if not isinstance(w, (int, float)) or w <= 0]
    if non_positive:
        violations.append(f"weights must be positive floats; invalid tickers: {sorted(non_positive)}")

    weight_sum = sum(target_weights.values())
    if abs(weight_sum - 100.0) > 0.01:
        violations.append(f"weights must sum to 100 (±0.01); got {weight_sum:.4f}")

    unknown = set(target_weights) - portfolio_tickers
    if unknown:
        violations.append(f"tickers not in portfolio: {sorted(unknown)}")

    if violations:
        raise ValueError("Invalid target weights — " + "; ".join(violations))


def compute_rebalance_trades(
    stocks: dict,
    target_weights: dict[str, float],
) -> dict:
    """Compute buy/sell trades needed to move the portfolio to target allocations.

    Tickers present in the portfolio but absent from target_weights are treated
    as having a target weight of 0 (full liquidation).
    """
    portfolio_tickers: set[str] = set(stocks.keys())
    validate_target_weights(target_weights, portfolio_tickers)

    # Inject zero-weight entries for tickers the caller omitted (full sells).
    target_weights_full: dict[str, float] = {
        ticker: target_weights.get(ticker, 0.0) for ticker in portfolio_tickers
    }

    total_value: float = sum(s["current_value"] for s in stocks.values())

    trades: list[dict] = []

    for ticker, stock in stocks.items():
        current_value: float = stock["current_value"]
        current_price: float = stock["current_price"]
        target_pct: float = target_weights_full[ticker]

        current_weight_pct: float = (current_value / total_value) * 100 if total_value else 0.0
        target_value: float = (target_pct / 100) * total_value
        trade_value: float = target_value - current_value
        trade_shares: float = trade_value / current_price if current_price else 0.0

        if trade_value > 0.01:
            action = "BUY"
        elif trade_value < -0.01:
            action = "SELL"
        else:
            action = "HOLD"

        trades.append(
            {
                "ticker": ticker,
                "action": action,
                "trade_value": trade_value,
                "trade_shares": trade_shares,
                "current_value": current_value,
                "target_value": target_value,
                "current_weight_pct": current_weight_pct,
                "target_weight_pct": target_pct,
            }
        )

    trades.sort(key=lambda t: (_ACTION_ORDER[t["action"]], t["ticker"]))

    total_buy_value: float = sum(t["trade_value"] for t in trades if t["action"] == "BUY")
    total_sell_value: float = sum(abs(t["trade_value"]) for t in trades if t["action"] == "SELL")

    instructions: list[str] = []
    for t in trades:
        if t["action"] == "SELL":
            instructions.append(
                f"🔴 Sell {format_currency(abs(t['trade_value']))} "
                f"({abs(t['trade_shares']):.2f} shares) of {t['ticker']}"
            )
        elif t["action"] == "BUY":
            instructions.append(
                f"🟢 Buy {format_currency(t['trade_value'])} "
                f"({t['trade_shares']:.2f} shares) of {t['ticker']}"
            )
        else:
            instructions.append(f"⚪ Hold {t['ticker']} — already at target")

    return {
        "trades": trades,
        "total_buy_value": total_buy_value,
        "total_sell_value": total_sell_value,
        "total_portfolio_value": total_value,
        "instructions": instructions,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    mock_stocks = {
        "AAPL": {"current_value": 50000.0, "current_price": 175.0},
        "TSLA": {"current_value": 30000.0, "current_price": 250.0},
        "MSFT": {"current_value": 20000.0, "current_price": 400.0},
    }

    result = compute_rebalance_trades(
        stocks=mock_stocks,
        target_weights={"AAPL": 40.0, "TSLA": 40.0, "MSFT": 20.0},
    )

    print(f"Total portfolio value: {result['total_portfolio_value']}")
    print(f"Total buy:  {result['total_buy_value']:.2f}")
    print(f"Total sell: {result['total_sell_value']:.2f}")
    print("\nInstructions:")
    for line in result["instructions"]:
        print(" ", line)
    print("\nTrades:")
    for t in result["trades"]:
        print(
            f"  {t['ticker']:5s}  {t['action']:4s}  "
            f"trade_value={t['trade_value']:>10.2f}  "
            f"trade_shares={t['trade_shares']:>7.2f}  "
            f"cur_wt={t['current_weight_pct']:.1f}%  "
            f"tgt_wt={t['target_weight_pct']:.1f}%"
        )
