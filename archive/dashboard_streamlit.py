"""Streamlit dashboard for the Portfolio Risk Analyser."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.portfolio_analytics import (
    compute_analytics,
    compute_benchmark_comparison,
    compute_portfolio_history,
)
from src.portfolio_fetcher import fetch_portfolio
from src.utils import format_currency, format_pct

_PIE_COLORS = [
    "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
    "#8B5CF6", "#06B6D4", "#EC4899", "#84CC16",
    "#F97316", "#14B8A6", "#6366F1", "#A78BFA",
]

BENCHMARK_OPTIONS: list[tuple[str, str]] = [
    ("Nifty 50", "^NSEI"),
    ("S&P 500", "^GSPC"),
    ("NASDAQ", "^IXIC"),
]

_DIVIDER_HTML = '<div style="height:1px;background:#2A2D3E;margin:24px 0;"></div>'

_RANGE_SELECTOR_STYLE: dict = dict(
    bgcolor="#1A1D2E",
    activecolor="#3B82F6",
    bordercolor="#2A2D3E",
    borderwidth=1,
    font=dict(color="#94A3B8", size=11),
    buttons=[
        dict(count=1, label="1M", step="month", stepmode="backward"),
        dict(count=3, label="3M", step="month", stepmode="backward"),
        dict(count=6, label="6M", step="month", stepmode="backward"),
        dict(step="all", label="1Y"),
    ],
)


def _divider() -> None:
    """Render a subtle horizontal rule."""
    st.markdown(_DIVIDER_HTML, unsafe_allow_html=True)


def _section_header(title: str) -> None:
    """Render an uppercase muted section label."""
    st.markdown(
        f'<p style="color:#94A3B8;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:2px;margin:0 0 16px 0;">'
        f'{title}</p>',
        unsafe_allow_html=True,
    )


def _metric_card(
    label: str, value: str, change: str = "", change_color: str = ""
) -> str:
    """Return HTML for a single premium metric card."""
    change_html = (
        f'<p style="color:{change_color};font-size:12px;margin:4px 0 0 0;">{change}</p>'
        if change and change_color
        else '<p style="font-size:12px;margin:4px 0 0 0;color:transparent;">·</p>'
    )
    return (
        '<div style="background:#1A1D2E;border:1px solid #2A2D3E;border-radius:12px;'
        'padding:16px 20px;box-shadow:0 4px 24px rgba(0,0,0,0.4);">'
        f'<p style="color:#94A3B8;font-size:11px;text-transform:uppercase;'
        f'letter-spacing:1px;margin:0 0 8px 0;">{label}</p>'
        f'<p style="color:#F1F5F9;font-size:22px;font-weight:700;margin:0;">{value}</p>'
        f'{change_html}'
        '</div>'
    )


def _is_market_open() -> bool:
    """Return True if NYSE is currently open (Mon–Fri, 13:30–20:00 UTC)."""
    now_utc = datetime.now(timezone.utc)
    if now_utc.weekday() >= 5:
        return False
    market_open = now_utc.replace(hour=13, minute=30, second=0, microsecond=0)
    market_close = now_utc.replace(hour=20, minute=0, second=0, microsecond=0)
    return market_open <= now_utc <= market_close


@st.cache_data(ttl=300)
def _cached_fetch(portfolio_json: str) -> tuple[dict, list[str]]:
    """Cached wrapper around fetch_portfolio; accepts a JSON-serialised portfolio list."""
    return fetch_portfolio(json.loads(portfolio_json))


_DEFAULT_PORTFOLIO: list[dict] = [
    {"ticker": "AAPL", "quantity": 10, "buy_price": 150.0},
    {"ticker": "MSFT", "quantity": 8, "buy_price": 280.0},
    {"ticker": "GOOGL", "quantity": 5, "buy_price": 140.0},
    {"ticker": "AMZN", "quantity": 6, "buy_price": 178.0},
    {"ticker": "TSLA", "quantity": 7, "buy_price": 200.0},
    {"ticker": "NVDA", "quantity": 4, "buy_price": 450.0},
    {"ticker": "META", "quantity": 5, "buy_price": 320.0},
    {"ticker": "JPM", "quantity": 8, "buy_price": 195.0},
    {"ticker": "GS", "quantity": 3, "buy_price": 380.0},
    {"ticker": "MS", "quantity": 6, "buy_price": 88.0},
    {"ticker": "NFLX", "quantity": 4, "buy_price": 550.0},
    {"ticker": "AMD", "quantity": 9, "buy_price": 120.0},
]


def _init_session_state() -> None:
    """Idempotently initialise all session state keys and auto-load default portfolio data."""
    defaults: dict = {
        "portfolio": _DEFAULT_PORTFOLIO,
        "analytics": None,
        "portfolio_history": None,
        "skipped": [],
        "comparison_df": None,
        "beta": None,
        "benchmark_label": BENCHMARK_OPTIONS[0][0],
        "data_loaded": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state["data_loaded"]:
        portfolio_json = json.dumps(st.session_state["portfolio"], sort_keys=True)
        with st.spinner("Loading portfolio data..."):
            portfolio_data, skipped = _cached_fetch(portfolio_json)
        st.session_state["skipped"] = skipped
        if portfolio_data:
            analytics = compute_analytics(portfolio_data)
            portfolio_history = compute_portfolio_history(portfolio_data)
            st.session_state["analytics"] = analytics
            st.session_state["portfolio_history"] = portfolio_history
            ticker_list = [e["ticker"] for e in st.session_state["portfolio"]]
            if ticker_list and not any(t.endswith((".NS", ".BO")) for t in ticker_list):
                auto_benchmark = BENCHMARK_OPTIONS[1]  # S&P 500
            else:
                auto_benchmark = BENCHMARK_OPTIONS[0]  # Nifty 50
            try:
                comparison_df, beta = compute_benchmark_comparison(
                    portfolio_history, auto_benchmark[1]
                )
                st.session_state["comparison_df"] = comparison_df
                st.session_state["beta"] = beta
                st.session_state["benchmark_label"] = auto_benchmark[0]
            except Exception:
                st.session_state["comparison_df"] = None
        st.session_state["data_loaded"] = True


def _render_sidebar() -> None:
    """Render the input panel in the sidebar and handle all portfolio actions."""
    with st.sidebar:
        st.markdown(
            '<p style="color:#94A3B8;font-size:10px;text-transform:uppercase;'
            'letter-spacing:2px;margin:16px 0 8px 0;">PORTFOLIO INPUT</p>',
            unsafe_allow_html=True,
        )

        ticker_input: str = st.text_input("Ticker", placeholder="e.g. RELIANCE.NS")
        quantity_input: int = int(
            st.number_input("Quantity", min_value=1, step=1, value=1)
        )
        buy_price_input: float = float(
            st.number_input(
                "Buy Price", min_value=0.01, step=0.01, value=100.0, format="%.2f"
            )
        )

        if st.button("＋ Add Stock", use_container_width=True):
            ticker = ticker_input.strip().upper()
            if ticker:
                st.session_state["portfolio"].append(
                    {
                        "ticker": ticker,
                        "quantity": quantity_input,
                        "buy_price": buy_price_input,
                    }
                )
                st.rerun()

        portfolio: list[dict] = st.session_state["portfolio"]

        if portfolio:
            st.markdown(
                '<p style="color:#94A3B8;font-size:10px;text-transform:uppercase;'
                'letter-spacing:2px;margin:16px 0 8px 0;">CURRENT PORTFOLIO</p>',
                unsafe_allow_html=True,
            )
            preview_df = pd.DataFrame(portfolio)
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

            for i in reversed(range(len(portfolio))):
                row = portfolio[i]
                if st.button(
                    f"✕ Remove {row['ticker']}",
                    key=f"remove_{i}",
                    use_container_width=True,
                ):
                    st.session_state["portfolio"].pop(i)
                    st.rerun()

        st.markdown(_DIVIDER_HTML, unsafe_allow_html=True)

        ticker_list = [entry["ticker"] for entry in st.session_state["portfolio"]]
        if ticker_list and not any(t.endswith((".NS", ".BO")) for t in ticker_list):
            default_benchmark_index = 1  # S&P 500
        else:
            default_benchmark_index = 0  # Nifty 50

        selected_benchmark: tuple[str, str] = st.selectbox(
            "Benchmark Index",
            options=BENCHMARK_OPTIONS,
            index=default_benchmark_index,
            format_func=lambda x: x[0],
        )
        selected_benchmark_label: str = selected_benchmark[0]
        selected_benchmark_ticker: str = selected_benchmark[1]

        if st.button(
            "🔍 Analyse Portfolio",
            disabled=len(portfolio) == 0,
            use_container_width=True,
            type="primary",
        ):
            portfolio_json = json.dumps(portfolio, sort_keys=True)
            with st.spinner("Fetching market data..."):
                portfolio_data, skipped = _cached_fetch(portfolio_json)
            st.session_state["skipped"] = skipped
            if not portfolio_data:
                st.error(
                    "No data could be fetched for any ticker. "
                    "Check ticker symbols or try again later."
                )
                return
            analytics = compute_analytics(portfolio_data)
            portfolio_history = compute_portfolio_history(portfolio_data)
            st.session_state["analytics"] = analytics
            st.session_state["portfolio_history"] = portfolio_history
            st.session_state["comparison_df"] = None
            st.session_state["beta"] = None
            st.rerun()

        if st.button(
            "📊 Compare vs Benchmark",
            disabled=st.session_state["analytics"] is None,
            use_container_width=True,
        ):
            portfolio_history = st.session_state["portfolio_history"]
            with st.spinner(f"Fetching {selected_benchmark_label} data..."):
                try:
                    comparison_df, beta = compute_benchmark_comparison(
                        portfolio_history, selected_benchmark_ticker
                    )
                    st.session_state["comparison_df"] = comparison_df
                    st.session_state["beta"] = beta
                    st.session_state["benchmark_label"] = selected_benchmark_label
                except Exception:
                    st.session_state["comparison_df"] = None
                    st.session_state["beta"] = None
            st.rerun()

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        if st.session_state["skipped"]:
            st.warning(
                f"Could not load data for: {', '.join(st.session_state['skipped'])}"
            )


def _render_summary_cards(portfolio_summary: dict, beta: Optional[float]) -> None:
    """Render seven summary metric cards as styled HTML in a single row."""
    cols = st.columns(7)
    ps = portfolio_summary

    ret = ps["overall_pct_return"]
    dd = ps["portfolio_max_drawdown"]
    sharpe = ps["portfolio_sharpe"]

    ret_color = "#10B981" if ret >= 0 else "#EF4444"
    sharpe_color = (
        "#10B981" if sharpe > 1 else ("#EF4444" if sharpe < 0 else "#94A3B8")
    )
    beta_valid = beta is not None and not (isinstance(beta, float) and pd.isna(beta))
    beta_str = f"{beta:.2f}" if beta_valid else "N/A"
    beta_color = (
        "#10B981" if (beta_valid and beta < 1)
        else ("#EF4444" if (beta_valid and beta > 1) else "#94A3B8")
    )

    with cols[0]:
        st.markdown(
            _metric_card("Total Invested", format_currency(ps["total_investment"])),
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            _metric_card("Current Value", format_currency(ps["total_current_value"])),
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            _metric_card("Total Return", format_pct(ret), format_pct(ret), ret_color),
            unsafe_allow_html=True,
        )
    with cols[3]:
        st.markdown(
            _metric_card(
                "Volatility (Ann.)",
                format_pct(ps["portfolio_volatility"]),
                "annualised",
                "#94A3B8",
            ),
            unsafe_allow_html=True,
        )
    with cols[4]:
        st.markdown(
            _metric_card("Sharpe Ratio", f"{sharpe:.2f}", "risk-adjusted", sharpe_color),
            unsafe_allow_html=True,
        )
    with cols[5]:
        st.markdown(
            _metric_card("Max Drawdown", format_pct(dd), format_pct(dd), "#EF4444"),
            unsafe_allow_html=True,
        )
    with cols[6]:
        st.markdown(
            _metric_card(
                "Beta vs Benchmark",
                beta_str,
                "vs benchmark" if beta_valid else "run comparison",
                beta_color,
            ),
            unsafe_allow_html=True,
        )


def _render_holdings_table(stocks: dict) -> None:
    """Render a styled holdings table with per-stock metrics."""
    n = len(stocks)
    st.markdown(
        f'<p style="color:#94A3B8;font-size:11px;text-transform:uppercase;'
        f'letter-spacing:1.5px;margin:0 0 12px 0;">HOLDINGS · {n} positions</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """<style>
        [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
        [data-testid="stDataFrame"] th {
            background: #0F1117 !important;
            color: #94A3B8 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        [data-testid="stDataFrame"] td { font-size: 13px !important; }
        </style>""",
        unsafe_allow_html=True,
    )

    rows = []
    for ticker, data in stocks.items():
        rows.append(
            {
                "Ticker": ticker,
                "Qty": data["quantity"],
                "Buy Price": data["buy_price"],
                "Current Price": data["current_price"],
                "Invested": data["investment_value"],
                "Current Value": data["current_value"],
                "Gain/Loss": data["gain_loss"],
                "Return %": data["pct_return"],
                "Volatility": data["volatility"],
                "Sharpe": data["sharpe_ratio"],
                "Max Drawdown": data["max_drawdown"],
            }
        )

    df = pd.DataFrame(rows)

    def _color_signed(val: object) -> str:
        """Return green or red CSS colour based on sign; empty string for None/NaN."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        return "color: #10B981" if float(val) >= 0 else "color: #EF4444"

    def _color_red(_: object) -> str:
        """Return red CSS colour unconditionally."""
        return "color: #EF4444"

    def _fmt_currency(val: object) -> str:
        """Format numeric value as currency string, or 'N/A' for missing data."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "N/A"
        return format_currency(float(val))

    def _fmt_pct(val: object) -> str:
        """Format numeric value as percentage string, or 'N/A' for missing data."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "N/A"
        return format_pct(float(val))

    def _fmt_sharpe(val: object) -> str:
        """Format Sharpe ratio to two decimal places, or 'N/A' for missing data."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "N/A"
        return f"{float(val):.2f}"

    styled = (
        df.style.format(
            {
                "Buy Price": _fmt_currency,
                "Current Price": _fmt_currency,
                "Invested": _fmt_currency,
                "Current Value": _fmt_currency,
                "Gain/Loss": _fmt_currency,
                "Return %": _fmt_pct,
                "Volatility": _fmt_pct,
                "Sharpe": _fmt_sharpe,
                "Max Drawdown": _fmt_pct,
            }
        )
        .map(_color_signed, subset=["Gain/Loss", "Return %"])
        .map(_color_red, subset=["Max Drawdown"])
    )

    st.dataframe(styled, use_container_width=True)


def _render_allocation_pie(stocks: dict) -> None:
    """Render a Plotly donut chart showing current value allocation by ticker."""
    tickers = list(stocks.keys())
    values = [data["current_value"] for data in stocks.values()]
    total = sum(values)

    fig = go.Figure(
        go.Pie(
            labels=tickers,
            values=values,
            hole=0.6,
            textinfo="label+percent",
            hoverinfo="label+value+percent",
            marker=dict(
                colors=_PIE_COLORS,
                line=dict(color="#0F1117", width=2),
            ),
            textfont=dict(color="#F1F5F9", size=11),
        )
    )
    fig.update_layout(
        annotations=[
            dict(
                text=f"<b>{format_currency(total)}</b>",
                x=0.5,
                y=0.5,
                font=dict(size=14, color="#F1F5F9"),
                showarrow=False,
            )
        ],
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            font=dict(color="#94A3B8", size=11),
            bgcolor="rgba(0,0,0,0)",
            x=1,
            y=0.5,
        ),
        margin=dict(t=0, b=0, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_portfolio_history(
    portfolio_history: pd.Series, total_investment: float
) -> None:
    """Render a Plotly line chart of portfolio value over time with fill and cost-basis."""
    dates = portfolio_history.index.tolist()
    values = portfolio_history.values.tolist()
    formatted_values = [format_currency(v) for v in values]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            name="Portfolio Value",
            line=dict(color="#3B82F6", width=2),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.1)",
            customdata=formatted_values,
            hovertemplate="%{customdata}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[dates[0], dates[-1]],
            y=[total_investment, total_investment],
            mode="lines",
            name="Cost Basis",
            line=dict(color="#94A3B8", width=1, dash="dash"),
            hovertemplate=(
                f"Cost Basis: {format_currency(total_investment)}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            color="#94A3B8",
            tickfont=dict(color="#94A3B8", size=11),
            linecolor="#2A2D3E",
            dtick="M1",
            tickformat="%b %y",
            rangeselector=_RANGE_SELECTOR_STYLE,
        ),
        yaxis=dict(
            title="Portfolio Value",
            showgrid=False,
            color="#94A3B8",
            tickfont=dict(color="#94A3B8", size=11),
            side="right",
            linecolor="#2A2D3E",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#94A3B8", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor="#1A1D2E",
            bordercolor="#2A2D3E",
            font=dict(color="#F1F5F9", size=12),
        ),
        margin=dict(t=30, b=0, l=0, r=60),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_return_bar(stocks: dict) -> None:
    """Render a horizontal Plotly bar chart of per-stock returns, sorted descending."""
    pairs = sorted(
        [(ticker, data["pct_return"]) for ticker, data in stocks.items()],
        key=lambda x: x[1],
    )
    tickers = [p[0] for p in pairs]
    returns = [p[1] for p in pairs]
    colors = ["#10B981" if v >= 0 else "#EF4444" for v in returns]

    fig = go.Figure(
        go.Bar(
            x=returns,
            y=tickers,
            orientation="h",
            marker=dict(color=colors),
            width=0.5,
            text=[f"{v:+.1f}%" for v in returns],
            textposition="outside",
            textfont=dict(color="#94A3B8", size=11),
            hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Return (%)",
            showgrid=False,
            zeroline=True,
            zerolinecolor="#2A2D3E",
            zerolinewidth=1,
            color="#94A3B8",
            tickfont=dict(color="#94A3B8", size=11),
            linecolor="#2A2D3E",
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color="#F1F5F9", size=12),
            linecolor="#2A2D3E",
        ),
        hoverlabel=dict(
            bgcolor="#1A1D2E",
            bordercolor="#2A2D3E",
            font=dict(color="#F1F5F9", size=12),
        ),
        margin=dict(t=0, b=0, l=0, r=80),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_benchmark_comparison(
    comparison_df: Optional[pd.DataFrame], benchmark_label: str
) -> None:
    """Render the benchmark comparison chart and outperformance callout.

    Shows a normalised line chart rebased to 100 and a three-column metric
    row with final portfolio value, benchmark value, and alpha.  Renders a
    warning and returns early if comparison_df is None or empty.
    """
    if comparison_df is None or comparison_df.empty:
        st.warning("Benchmark data unavailable. Try a different index or refresh.")
        return

    fig = go.Figure()
    # Benchmark first so portfolio fill="tonexty" fills between the two lines
    fig.add_trace(
        go.Scatter(
            x=comparison_df.index,
            y=comparison_df["benchmark_normalised"],
            name=benchmark_label,
            line=dict(color="#F59E0B", width=1.5, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=comparison_df.index,
            y=comparison_df["portfolio_normalised"],
            name="My Portfolio",
            line=dict(color="#3B82F6", width=2),
            fill="tonexty",
            fillcolor="rgba(16,185,129,0.05)",
        )
    )
    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color="#2A2D3E",
        annotation_text="Start",
        annotation_position="right",
        annotation_font_color="#94A3B8",
    )
    fig.update_layout(
        title=dict(
            text=f"Portfolio vs {benchmark_label} (Rebased to 100)",
            font=dict(color="#F1F5F9", size=14),
        ),
        yaxis=dict(
            title="Normalised Value",
            showgrid=False,
            color="#94A3B8",
            tickfont=dict(color="#94A3B8", size=11),
            linecolor="#2A2D3E",
        ),
        xaxis=dict(
            showgrid=False,
            color="#94A3B8",
            tickfont=dict(color="#94A3B8", size=11),
            linecolor="#2A2D3E",
            rangeselector=_RANGE_SELECTOR_STYLE,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1A1D2E",
            bordercolor="#2A2D3E",
            font=dict(color="#F1F5F9", size=12),
        ),
        legend=dict(
            font=dict(color="#94A3B8", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=0, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    final_portfolio = comparison_df["portfolio_normalised"].iloc[-1]
    final_benchmark = comparison_df["benchmark_normalised"].iloc[-1]
    outperformance = final_portfolio - final_benchmark
    alpha_color = "#10B981" if outperformance >= 0 else "#EF4444"
    alpha_label = "outperformance" if outperformance >= 0 else "underperformance"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            _metric_card("Portfolio (Rebased)", f"{final_portfolio:.1f}"),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            _metric_card("Benchmark (Rebased)", f"{final_benchmark:.1f}"),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            _metric_card(
                f"Alpha vs {benchmark_label}",
                f"{outperformance:+.1f} pts",
                alpha_label,
                alpha_color,
            ),
            unsafe_allow_html=True,
        )


def main() -> None:
    """Entry point for the Portfolio Risk Analyser dashboard."""
    st.set_page_config(
        page_title="PortfolioIQ",
        layout="wide",
        page_icon="📊",
    )

    # ── Global CSS ────────────────────────────────────────────────────────────
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }
.main { background: #0F1117 !important; }
.block-container { padding: 24px 32px !important; max-width: 100% !important; }
h1 { color: #F1F5F9 !important; font-size: 28px !important; font-weight: 700 !important; }
p { color: #94A3B8 !important; }
[data-testid="stMetricValue"] { font-size: 22px !important; }

[data-testid="stSidebar"] {
    background: #1A1D2E !important;
    border-right: 1px solid #2A2D3E !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: #1A1D2E !important;
    border: 1px solid #2A2D3E !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    transition: border-color 0.15s;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #2A2D3E !important;
    border-color: #3B82F6 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

    # ── Navbar ────────────────────────────────────────────────────────────────
    open_status = _is_market_open()
    dot_color = "#10B981" if open_status else "#EF4444"
    status_text = "Market Open" if open_status else "Market Closed"
    pulse_css = (
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}"
        if open_status
        else ""
    )
    dot_anim = "animation:pulse 2s infinite;" if open_status else ""
    st.markdown(
        f"""<style>{pulse_css}</style>
<div style="background:#1A1D2E;border-bottom:1px solid #2A2D3E;
            padding:12px 24px;margin-bottom:24px;border-radius:12px;
            display:flex;align-items:center;justify-content:space-between;">
  <span style="color:#F1F5F9;font-size:18px;font-weight:700;">
    📊 PortfolioIQ
  </span>
  <span style="display:flex;align-items:center;gap:8px;">
    <span style="width:8px;height:8px;background:{dot_color};border-radius:50%;
                 display:inline-block;{dot_anim}"></span>
    <span style="color:#94A3B8;font-size:13px;">{status_text}</span>
  </span>
  <span style="color:#94A3B8;font-size:13px;">Live Data · Yahoo Finance</span>
</div>""",
        unsafe_allow_html=True,
    )

    _init_session_state()
    _render_sidebar()

    analytics: Optional[dict] = st.session_state["analytics"]
    if analytics is None:
        st.info(
            "Add stocks in the sidebar and click **🔍 Analyse Portfolio** to begin."
        )
        return

    portfolio_history: pd.Series = st.session_state["portfolio_history"]
    portfolio_summary: dict = analytics["portfolio_summary"]
    stocks: dict = analytics["stocks"]

    _render_summary_cards(portfolio_summary, st.session_state["beta"])

    if st.session_state["skipped"]:
        st.warning(
            f"Could not load data for: {', '.join(st.session_state['skipped'])}"
        )

    _divider()
    _render_holdings_table(stocks)

    _divider()
    col1, col2 = st.columns(2)
    with col1:
        _section_header("Asset Allocation")
        _render_allocation_pie(stocks)
    with col2:
        _section_header("Portfolio Value Over Time")
        _render_portfolio_history(
            portfolio_history, portfolio_summary["total_investment"]
        )

    _divider()
    _section_header("Return by Stock")
    _render_return_bar(stocks)

    _divider()
    _section_header("Portfolio vs Benchmark")
    _render_benchmark_comparison(
        st.session_state["comparison_df"],
        st.session_state["benchmark_label"],
    )


if __name__ == "__main__":
    main()
