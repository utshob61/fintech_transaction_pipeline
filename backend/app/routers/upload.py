"""
upload.py
---------
Ingestion endpoints: upload a CSV file, or POST raw JSON transactions.
Both run the same ETL pipeline (transform -> fraud-flag -> load) so
behavior is identical regardless of source — matching the "Extract"
flexibility required (CSV or API/JSON input).
"""

import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import create_engine

from app.database import DATABASE_URL
from app.schemas import IngestResponse, TransactionIn
from etl.pipeline import run_pipeline_from_csv, run_pipeline_from_records

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["Ingestion"])

engine = create_engine(DATABASE_URL)


@router.post("/csv", response_model=IngestResponse, summary="Upload a transactions CSV file")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        report = run_pipeline_from_csv(tmp_path, engine)
        return report

    except ValueError as e:
        # e.g. missing required columns
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("CSV ingestion failed")
        raise HTTPException(status_code=500, detail="Failed to process the uploaded file.")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/json", response_model=IngestResponse, summary="Ingest transactions as a JSON list")
async def upload_json(transactions: list[TransactionIn]):
    if not transactions:
        raise HTTPException(status_code=400, detail="Transaction list cannot be empty.")

    try:
        records = [t.model_dump() for t in transactions]
        report = run_pipeline_from_records(records, engine)
        return report
    except Exception:
        logger.exception("JSON ingestion failed")
        raise HTTPException(status_code=500, detail="Failed to process the submitted transactions.")
