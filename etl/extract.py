"""
extract.py
----------
Extract step of the ETL pipeline.

Responsible ONLY for getting raw data into a pandas DataFrame.
No cleaning/validation happens here — that's transform.py's job.
"""

import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "transaction_id",
    "user_id",
    "merchant_id",
    "amount",
    "payment_method",
    "transaction_status",
    "timestamp",
]


def extract_from_csv(file_path: str) -> pd.DataFrame:
    """
    Read a transactions CSV file into a DataFrame.

    Raises:
        ValueError: if required columns are missing.
    """
    logger.info("Extracting transactions from CSV: %s", file_path)
    df = pd.read_csv(file_path)
    _validate_columns(df)
    logger.info("Extracted %d raw rows from CSV.", len(df))
    return df


def extract_from_api(api_url: str, timeout: int = 10) -> pd.DataFrame:
    """
    Fetch transactions from a JSON API endpoint.

    Expects the endpoint to return either:
      - a JSON list of transaction objects, OR
      - a JSON object with a "transactions" key containing that list.
    """
    logger.info("Extracting transactions from API: %s", api_url)
    response = requests.get(api_url, timeout=timeout)
    response.raise_for_status()

    payload = response.json()
    records = payload.get("transactions", payload) if isinstance(payload, dict) else payload

    df = pd.DataFrame(records)
    _validate_columns(df)
    logger.info("Extracted %d raw rows from API.", len(df))
    return df


def extract_from_json_records(records: list) -> pd.DataFrame:
    """Build a DataFrame from a list of dicts (e.g. a FastAPI request body)."""
    df = pd.DataFrame(records)
    _validate_columns(df)
    return df


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Input data is missing required columns: {missing}")
