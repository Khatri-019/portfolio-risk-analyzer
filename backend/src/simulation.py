"""Monte Carlo simulation for portfolio value projection."""

import logging
import math

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

N_SIMULATIONS = 1000
N_TRADING_DAYS = 252
PERCENTILES = [10, 50, 90]
RANDOM_SEED = 42

MIN_HISTORY_POINTS = 30


def run_monte_carlo(
    portfolio_history: pd.Series,
    n_simulations: int = N_SIMULATIONS,
    n_days: int = N_TRADING_DAYS,
) -> dict:
    """Project portfolio value over n_days using geometric Brownian motion parameters fit to history.

    Draws daily returns from a normal distribution parameterised by the historical
    mean and std, compounds them into price paths, and computes risk metrics on the
    distribution of final values.
    """
    if len(portfolio_history) < MIN_HISTORY_POINTS:
        raise ValueError(
            f"portfolio_history has {len(portfolio_history)} data points; "
            f"minimum required is {MIN_HISTORY_POINTS}."
        )

    daily_returns: pd.Series = portfolio_history.pct_change().dropna()
    mu: float = daily_returns.mean()
    sigma: float = daily_returns.std()

    start_value: float = float(portfolio_history.iloc[-1])

    np.random.seed(RANDOM_SEED)
    sim_returns: np.ndarray = np.random.normal(mu, sigma, (n_days, n_simulations))

    cum_product: np.ndarray = np.cumprod(1 + sim_returns, axis=0)
    paths_body: np.ndarray = start_value * cum_product

    paths: np.ndarray = np.vstack(
        [np.full((1, n_simulations), start_value), paths_body]
    )

    final_values: np.ndarray = paths[-1]

    p10, p50, p90 = np.percentile(final_values, PERCENTILES)
    var_95: float = start_value - float(np.percentile(final_values, 5))
    prob_profit: float = float((final_values > start_value).mean() * 100)

    return {
        "paths": paths,
        "current_value": start_value,
        "p10": float(p10),
        "p50": float(p50),
        "p90": float(p90),
        "var_95": var_95,
        "prob_profit": prob_profit,
        "mu": float(mu),
        "sigma": float(sigma),
        "n_simulations": n_simulations,
        "n_days": n_days,
    }


def get_simulation_summary(simulation_result: dict) -> dict:
    """Derive human-readable risk metrics from a run_monte_carlo result dict.

    Classifies annualised volatility into Low / Moderate / High Risk buckets
    so the dashboard can surface a plain-English label alongside the numbers.
    """
    current_value: float = simulation_result["current_value"]
    sigma: float = simulation_result["sigma"]

    annualised_vol: float = sigma * math.sqrt(N_TRADING_DAYS)

    if annualised_vol < 0.15:
        risk_label = "Low Risk"
    elif annualised_vol < 0.25:
        risk_label = "Moderate Risk"
    else:
        risk_label = "High Risk"

    return {
        "expected_value": simulation_result["p50"],
        "upside": simulation_result["p90"] - current_value,
        "downside": current_value - simulation_result["p10"],
        "var_95": simulation_result["var_95"],
        "prob_profit": simulation_result["prob_profit"],
        "risk_label": risk_label,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
