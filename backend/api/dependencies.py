"""FastAPI dependency functions for API key injection."""

import os

from fastapi import HTTPException


def get_groq_api_key() -> str:
    """Read GROQ_API_KEY from environment; raise 500 if absent or empty."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")
    return key


def get_news_api_key() -> str:
    """Read NEWS_API_KEY from environment; raise 500 if absent or empty."""
    key = os.environ.get("NEWS_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=500, detail="NEWS_API_KEY is not configured")
    return key
