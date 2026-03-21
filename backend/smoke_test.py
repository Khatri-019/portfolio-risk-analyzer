import sys, os
sys.path.insert(0, '.')
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

from src.sentiment import analyse_portfolio_sentiment

news_api_key = os.environ.get("NEWS_API_KEY", "")

result = analyse_portfolio_sentiment(
    {
        "AAPL": "Apple Inc",
        "MSFT": "Microsoft",
        "NVDA": "NVIDIA",
    },
    news_api_key
)

print(f"Portfolio Sentiment : {result['portfolio_sentiment']}")
print(f"Summary             : {result['summary']}")
print()
for ticker, data in result['ticker_sentiments'].items():
    print(f"{ticker:6} | {data['overall_sentiment']:8} | score: {data['sentiment_score']:+.3f} | headlines: {data['headlines_analysed']}")
