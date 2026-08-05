import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine as _create_engine, text
from fastapi.responses import Response

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

    db_url = os.getenv("DATABASE_URL")
    remote_db_ok = False

    if not db_url:
        logger.warning("No DATABASE_URL set; using in-memory SQLite fallback.")
    else:
        try:
            # quick connectivity check (fast-fail in serverless environments)
            test_engine = _create_engine(db_url, connect_args={"connect_timeout": 2})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("Remote database reachable.")
            remote_db_ok = True
        except Exception:
            logger.warning(
                "Remote DATABASE_URL is unreachable; continuing startup with fallback engine."
            )

    if remote_db_ok:
        init_database()
    else:
        logger.info("Skipping remote schema initialization because the remote database is unavailable.")

    Base.metadata.create_all(bind=engine)
    logger.info("Database ready.")

    # Auto-seed the database with sample data if it's an in-memory SQLite and empty.
    # This ensures a consistent "demo" experience on stateless platforms like Vercel.
    if not remote_db_ok:
        try:
            with engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
                if count == 0:
                    logger.info("Seeding in-memory database with sample data...")
                    from etl.pipeline import run_pipeline_from_csv
                    sample_csv = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_transactions.csv")
                    if os.path.exists(sample_csv):
                        run_pipeline_from_csv(sample_csv, engine)
                        logger.info("Seeding complete.")
                    else:
                        logger.warning(f"Sample data not found at {sample_csv}")
        except Exception as e:
            logger.warning(f"Failed to seed database: {e}")

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


@app.get("/favicon.ico")
@app.get("/favicon.png")
async def favicon():
    """Return an empty response for favicon requests to avoid unnecessary errors
    in serverless environments where static files aren't present.
    """
    return Response(status_code=204)

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