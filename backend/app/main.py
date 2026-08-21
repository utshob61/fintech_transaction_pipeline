import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text
from fastapi.responses import FileResponse, Response

from app.database import Base, engine
from app.logging_config import setup_logging
from app.models import *
from app.schemas import *
from app.routers import analytics, chat, transactions, upload

# Import init_database from the root database package
from database.init_db import init_database

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Fintech Transaction Analytics API...")

    db_url = os.getenv("DATABASE_URL")
    
    # On Vercel (serverless), we want to avoid heavy DB init on every request.
    # We only run create_all which is fast if tables already exist.
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified.")
    except Exception as e:
        logger.warning(f"Database sync skipped or failed: {e}")

    # Auto-seed check: only runs if using in-memory SQLite (no DATABASE_URL)
    if not db_url:
        try:
            with engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
                if count == 0:
                    from etl.pipeline import run_pipeline_from_csv
                    sample_csv = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_transactions.csv")
                    if os.path.exists(sample_csv):
                        run_pipeline_from_csv(sample_csv, engine)
                        logger.info("In-memory database seeded.")
        except Exception:
            pass

    yield
    logger.info("Shutting down Fintech Transaction Analytics API.")
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
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(upload.router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(chat.router)


@app.get("/", tags=["Health"])
async def health_check():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "..", "public", "index.html"))


@app.get("/dashboard.js", include_in_schema=False)
async def dashboard_script():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "..", "public", "dashboard.js"))
