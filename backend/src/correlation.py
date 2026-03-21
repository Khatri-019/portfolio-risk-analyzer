"""Correlation analysis and diversification scoring for portfolio holdings."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_correlation_matrix(stocks: dict) -> pd.DataFrame:
    """Compute pairwise Pearson correlation matrix of daily returns.

    Extracts daily_returns from each ticker in the stocks dict, aligns all
    series on common dates via inner join, and returns the correlation matrix.
    Raises ValueError if fewer than 2 stocks are provided.
    """
    if len(stocks) < 2:
        raise ValueError("Need at least 2 stocks for correlation")

    return_series: list[pd.Series] = []
    for ticker, data in stocks.items():
        series: pd.Series = data["daily_returns"].copy()
        series.name = ticker
        return_series.append(series)

    combined: pd.DataFrame = pd.concat(return_series, axis=1).dropna()
    return combined.corr()


def compute_diversification_score(
    correlation_matrix: pd.DataFrame,
    stocks: dict,
) -> dict:
    """Return a diversification score and breakdown for the portfolio.

    Combines a correlation component (60%) and a concentration component (40%)
    into a single score from 0–100, where higher is better diversified.
    """
    matrix: np.ndarray = correlation_matrix.values
    rows, cols = np.triu_indices_from(matrix, k=1)
    upper_triangle_values: np.ndarray = matrix[rows, cols]
    avg_corr: float = float(upper_triangle_values.mean())

    correlation_score: float = max(0.0, min(100.0, (1 - avg_corr) * 100))

    total_current_value: float = sum(
        stocks[t]["current_value"] for t in stocks
    )
    weights: dict[str, float] = {
        t: stocks[t]["current_value"] / total_current_value for t in stocks
    }
    max_weight_ticker: str = max(weights, key=lambda t: weights[t])
    max_weight: float = weights[max_weight_ticker]

    concentration_score: float = max(0.0, min(100.0, (1 - max_weight) * 100))

    final_score: float = round(
        (0.6 * correlation_score) + (0.4 * concentration_score), 1
    )

    if final_score >= 65:
        label = "Well Diversified"
    elif final_score >= 40:
        label = "Moderately Diversified"
    else:
        label = "Poorly Diversified"

    explanation: str = (
        f"Average correlation of {avg_corr:.2f} with {max_weight_ticker} holding "
        f"{max_weight * 100:.1f}% of portfolio indicates "
        f"{'low' if final_score >= 65 else 'moderate' if final_score >= 40 else 'high'} "
        f"sector concentration."
    )

    return {
        "score": final_score,
        "label": label,
        "explanation": explanation,
        "avg_correlation": round(avg_corr, 4),
        "max_concentration": round(max_weight,4),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
