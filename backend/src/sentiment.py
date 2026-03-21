"""News sentiment analysis using FinBERT for portfolio holdings."""

import logging
import os

import certifi
import requests
from dotenv import load_dotenv
from transformers import pipeline

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)

FINBERT_MODEL = "ProsusAI/finbert"
MAX_HEADLINES_PER_TICKER = 5
NEWS_API_URL = "https://newsapi.org/v2/everything"
SENTIMENT_POSITIVE_THRESHOLD = 0.2
SENTIMENT_NEGATIVE_THRESHOLD = -0.2
HEADLINE_MAX_CHARS = 512

_finbert_pipeline = None


def load_finbert():
    """Load FinBERT sentiment pipeline, caching it at module level after first load."""
    global _finbert_pipeline
    if _finbert_pipeline is None:
        logger.warning("Loading FinBERT model — this may take 30-60 seconds on first run...")
        _finbert_pipeline = pipeline(
            "text-classification",
            model=FINBERT_MODEL,
            tokenizer=FINBERT_MODEL,
        )
    return _finbert_pipeline


def fetch_headlines(
    ticker: str,
    company_name: str,
    api_key: str,
    max_results: int = MAX_HEADLINES_PER_TICKER,
) -> list[str]:
    """Fetch recent news headlines for a ticker using NewsAPI.

    Returns an empty list on any failure — never raises.
    """
    params = {
        "q": f"{ticker} OR {company_name} stock",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "apiKey": api_key,
    }
    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        if response.status_code != 200:
            logger.warning(
                "NewsAPI returned status %d for ticker '%s'.",
                response.status_code,
                ticker,
            )
            return []
        articles = response.json().get("articles", [])
        return [a["title"] for a in articles if a.get("title") is not None]
    except Exception as e:
        logger.warning("NewsAPI fetch failed for ticker '%s': %s", ticker, e)
        return []


def classify_headlines(headlines: list[str]) -> list[dict]:
    """Run FinBERT on each headline and return label + confidence per headline."""
    if not headlines:
        return []

    finbert = load_finbert()
    results: list[dict] = []
    for headline in headlines:
        truncated = headline[:HEADLINE_MAX_CHARS]
        prediction = finbert(truncated)[0]
        results.append(
            {
                "headline": headline,
                "sentiment": prediction["label"].lower(),
                "confidence": round(prediction["score"], 4),
            }
        )
    return results


def analyse_ticker_sentiment(
    ticker: str,
    company_name: str,
    news_api_key: str,
) -> dict:
    """Full sentiment pipeline for one ticker.

    Returns neutral sentiment with zero headlines when NewsAPI is unavailable.
    """
    headlines = fetch_headlines(ticker, company_name, news_api_key)
    classified = classify_headlines(headlines)

    positive_count = sum(1 for h in classified if h["sentiment"] == "positive")
    neutral_count = sum(1 for h in classified if h["sentiment"] == "neutral")
    negative_count = sum(1 for h in classified if h["sentiment"] == "negative")

    if classified:
        direction_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        total_confidence = sum(h["confidence"] for h in classified)
        weighted_sum = sum(
            h["confidence"] * direction_map[h["sentiment"]] for h in classified
        )
        sentiment_score = weighted_sum / total_confidence if total_confidence > 0 else 0.0
    else:
        sentiment_score = 0.0

    if sentiment_score > SENTIMENT_POSITIVE_THRESHOLD:
        overall_sentiment = "positive"
    elif sentiment_score < SENTIMENT_NEGATIVE_THRESHOLD:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "neutral"

    return {
        "ticker": ticker,
        "company_name": company_name,
        "headlines_analysed": len(classified),
        "overall_sentiment": overall_sentiment,
        "sentiment_score": round(sentiment_score, 4),
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "headlines": classified,
    }


def analyse_portfolio_sentiment(
    tickers_and_names: dict[str, str],
    news_api_key: str,
) -> dict:
    """Run sentiment analysis across all portfolio holdings.

    tickers_and_names maps ticker symbols to company names, e.g.
    {"AAPL": "Apple Inc", "TSLA": "Tesla Inc"}.
    Portfolio-level sentiment is determined by majority vote; ties favour "neutral".
    """
    ticker_sentiments: dict[str, dict] = {}
    for ticker, company_name in tickers_and_names.items():
        ticker_sentiments[ticker] = analyse_ticker_sentiment(
            ticker, company_name, news_api_key
        )

    vote_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for result in ticker_sentiments.values():
        label = result["overall_sentiment"]
        vote_counts[label] += 1

    # Tie-break order: neutral > positive > negative (conservative for risk context)
    portfolio_sentiment = max(
        vote_counts,
        key=lambda label: (vote_counts[label], label == "neutral", label == "positive"),
    )

    total = len(ticker_sentiments)
    positive_count = vote_counts["positive"]
    summary = f"{positive_count}/{total} holdings show positive sentiment"

    return {
        "ticker_sentiments": ticker_sentiments,
        "portfolio_sentiment": portfolio_sentiment,
        "summary": summary,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
