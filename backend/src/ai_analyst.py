"""AI-powered portfolio health report generation via Groq API."""
import json
import logging
from groq import Groq
import os
import certifi
from dotenv import load_dotenv

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"

_DEFAULT_N_SIMULATIONS = 1000

REQUIRED_KEYS: frozenset[str] = frozenset(
    {"health_score", "health_label", "summary", "risk_factors", "suggestions"}
)


def build_portfolio_prompt(
    portfolio_summary: dict,
    diversification: dict,
    simulation_summary: dict,
) -> str:
    """Build a structured natural-language prompt from the three analytics dicts.

    Reads n_simulations from simulation_summary when present so the header
    reflects the actual run; falls back to _DEFAULT_N_SIMULATIONS otherwise.
    """
    n_sims: int = simulation_summary.get("n_simulations", _DEFAULT_N_SIMULATIONS)

    # portfolio_summary values — volatility/sharpe/drawdown/beta may be None
    total_investment: float = portfolio_summary.get("total_investment", 0.0)
    total_current_value: float = portfolio_summary.get("total_current_value", 0.0)
    total_gain_loss: float = portfolio_summary.get("total_gain_loss", 0.0)
    overall_pct_return: float = portfolio_summary.get("overall_pct_return", 0.0)
    portfolio_volatility = portfolio_summary.get("portfolio_volatility")
    portfolio_sharpe = portfolio_summary.get("portfolio_sharpe")
    portfolio_max_drawdown = portfolio_summary.get("portfolio_max_drawdown")
    beta = portfolio_summary.get("beta")

    # diversification values
    div_score: float = diversification.get("score", 0.0)
    div_label: str = diversification.get("label", "Unknown")
    avg_corr: float = diversification.get("avg_correlation", 0.0)
    max_concentration: float = diversification.get("max_concentration", 0.0)

    # simulation_summary values
    expected_value: float = simulation_summary.get("expected_value", 0.0)
    upside: float = simulation_summary.get("upside", 0.0)
    downside: float = simulation_summary.get("downside", 0.0)
    var_95: float = simulation_summary.get("var_95", 0.0)
    prob_profit: float = simulation_summary.get("prob_profit", 0.0)
    risk_label: str = simulation_summary.get("risk_label", "Unknown")

    def _fmt(val, spec: str = ".2f") -> str:
        return f"{val:{spec}}" if val is not None else "N/A"

    return (
        "You are a professional portfolio risk analyst. Analyse the following portfolio "
        "data and return a JSON object only — no prose outside the JSON.\n"
        "\n"
        "PORTFOLIO SUMMARY:\n"
        f"- Total invested: \u20b9{total_investment:,.2f}\n"
        f"- Current value: \u20b9{total_current_value:,.2f}\n"
        f"- Total gain/loss: \u20b9{total_gain_loss:,.2f}\n"
        f"- Overall return: {_fmt(overall_pct_return)}%\n"
        f"- Volatility (annualised): {_fmt(portfolio_volatility)}\n"
        f"- Sharpe ratio: {_fmt(portfolio_sharpe)}\n"
        f"- Max drawdown: {_fmt(portfolio_max_drawdown)}%\n"
        f"- Beta: {_fmt(beta)}\n"
        "\n"
        "DIVERSIFICATION:\n"
        f"- Score: {div_score} / 100 \u2014 {div_label}\n"
        f"- Average pairwise correlation: {avg_corr:.4f}\n"
        f"- Largest single-stock weight: {max_concentration * 100:.1f}%\n"
        "\n"
        f"MONTE CARLO SIMULATION ({n_sims:,} paths, 252 trading days):\n"
        f"- Median projected value: \u20b9{expected_value:,.2f}\n"
        f"- Upside scenario (90th percentile above current): \u20b9{upside:,.2f}\n"
        f"- Downside scenario (10th percentile below current): \u20b9{downside:,.2f}\n"
        f"- Value at Risk (95%): \u20b9{var_95:,.2f}\n"
        f"- Probability of profit: {prob_profit:.1f}%\n"
        f"- Risk classification: {risk_label}\n"
        "\n"
        "Return this exact JSON schema:\n"
        "{\n"
        '  "health_score": <integer 0\u2013100>,\n'
        '  "health_label": <one of "Excellent" | "Good" | "Fair" | "Poor" | "Critical">,\n'
        '  "summary": <2\u20133 sentence overall assessment>,\n'
        '  "risk_factors": [<up to 4 concise strings identifying key risks>],\n'
        '  "suggestions": [<up to 4 actionable recommendation strings>]\n'
        "}"
    )


def generate_portfolio_health_report(
    portfolio_summary: dict,
    diversification: dict,
    simulation_summary: dict,
    api_key: str,
) -> dict:
    """Call Groq API and return a parsed JSON health report for the portfolio.

    Builds a structured prompt from the three analytics dicts, submits it to
    Groq with json_object response_format enforced, validates all required keys,
    and returns the parsed dict.  Never raises — returns an error dict on any failure.
    """
    _error_base: dict = {
        "risk_factors": [],
        "suggestions": [],
        "summary": "Analysis unavailable. Check API key.",
        "health_score": 0,
        "health_label": "Unknown",
    }

    prompt = build_portfolio_prompt(portfolio_summary, diversification, simulation_summary)

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        response_text: str = response.choices[0].message.content
    except Exception as e:
        logger.warning("Groq API call failed: %s", e)
        return {**_error_base, "error": str(e)}

    try:
        parsed: dict = json.loads(response_text)
        missing = REQUIRED_KEYS - parsed.keys()
        if missing:
            raise ValueError(f"Response missing required keys: {missing}")
        return parsed
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse Groq response: %s", e)
        return {**_error_base, "error": str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
