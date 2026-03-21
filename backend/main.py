"""FastAPI application entry point — routing and middleware only."""

import os

import certifi
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from api.routers.portfolio import router as portfolio_router
from api.routers.analysis import router as analysis_router
from api.routers.system import router as system_router

app = FastAPI(title="Portfolio Risk Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(system_router, prefix="/api")
