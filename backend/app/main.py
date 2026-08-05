import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.logging_config import setup_logging
from app.models import *
from app.schemas import *
from app.routers import analytics, transactions, upload

# Import init_database from the root database package
from database.init_db import init_database

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Fintech Transaction Analytics API...")
    try:
        init_database()  # CREATE TABLE IF NOT EXISTS
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(transactions.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "fintech-transaction-analytics-api"
    }