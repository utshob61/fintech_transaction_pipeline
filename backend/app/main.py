"""
main.py
-------
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Swagger docs available at /docs, ReDoc at /redoc (both generated
automatically by FastAPI from the Pydantic schemas + route definitions).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.logging_config import setup_logging
from app.routers import analytics, transactions, upload
from database.init_db import init_database

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Fintech Transaction Analytics API...")
    try:
        init_database()  # idempotent — CREATE TABLE IF NOT EXISTS
        Base.metadata.create_all(bind=engine)
        logger.info("Database ready.")
    except Exception:
        logger.exception("Could not initialize database on startup.")
    yield
    logger.info("Shutting down Fintech Transaction Analytics API.")


app = FastAPI(
    title="Fintech Transaction Analytics Pipeline",
    description=(
        "A bKash/Nagad-style transaction monitoring & analytics API: "
        "ingestion, ETL, fraud flagging, and analytics endpoints."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the Streamlit dashboard (running on a different origin/container)
# to call this API directly from the browser if needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(transactions.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"], summary="Health check")
def health_check():
    return {"status": "ok", "service": "fintech-transaction-analytics-api"}
