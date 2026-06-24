"""
transform.py
------------
Transform step of the ETL pipeline.

Takes raw extracted data and returns clean, analysis-ready data:
  - removes duplicate transaction_ids
  - handles missing values
  - converts timestamps to proper datetime
  - standardizes payment method names
  - validates/drops negative or invalid amounts

Every cleaning step logs how many rows it affected, and the pipeline
returns a small "report" dict so callers (API responses, logs) can
tell the user exactly what happened to their data.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

VALID_STATUSES = {"SUCCESS", "FAILED", "PENDING"}

# Maps messy/real-world variants -> a single standardized label.
PAYMENT_METHOD_MAP = {
    "bkash": "bKash",
    "b-kash": "bKash",
    "nagad": "Nagad",
    "rocket": "Rocket",
    "card": "Card",
    "credit card": "Card",
    "debit card": "Card",
    "bank": "Bank Transfer",
    "bank transfer": "Bank Transfer",
    "cash": "Cash",
}


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Run the full cleaning/validation pipeline on a raw transactions DataFrame.

    Returns:
        (clean_df, report) where report is a dict summarizing what was
        removed/fixed at each stage — useful for API responses & logging.
    """
    report = {"input_rows": len(df)}
    df = df.copy()

    df, report["duplicates_removed"] = _remove_duplicates(df)
    df, report["missing_value_rows_dropped"] = _handle_missing_values(df)
    df = _convert_timestamps(df)
    df = _standardize_payment_methods(df)
    df = _standardize_status(df)
    df, report["invalid_amount_rows_dropped"] = _validate_amounts(df)

    report["output_rows"] = len(df)
    logger.info("Transform complete: %s", report)
    return df, report


def _remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    removed = before - len(df)
    if removed:
        logger.info("Removed %d duplicate transaction_id rows.", removed)
    return df, removed


def _handle_missing_values(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Critical fields can't be guessed — rows missing them are dropped.
    Non-critical fields get sensible defaults instead of being dropped."""
    before = len(df)

    critical_fields = ["transaction_id", "user_id", "merchant_id", "amount", "timestamp"]
    df = df.dropna(subset=critical_fields)

    # payment_method / transaction_status missing -> fill with explicit "UNKNOWN"
    # rather than dropping the whole transaction.
    df["payment_method"] = df["payment_method"].fillna("UNKNOWN")
    df["transaction_status"] = df["transaction_status"].fillna("UNKNOWN")

    dropped = before - len(df)
    if dropped:
        logger.info("Dropped %d rows missing critical fields.", dropped)
    return df, dropped


def _convert_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # Any row where the timestamp couldn't be parsed is unusable for
    # time-based analytics, so drop it (after logging how many).
    bad = df["timestamp"].isna().sum()
    if bad:
        logger.warning("Dropping %d rows with unparseable timestamps.", bad)
    df = df.dropna(subset=["timestamp"])
    return df


def _standardize_payment_methods(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df["payment_method"].astype(str).str.strip().str.lower()
    df["payment_method"] = normalized.map(PAYMENT_METHOD_MAP).fillna(df["payment_method"])
    return df


def _standardize_status(df: pd.DataFrame) -> pd.DataFrame:
    df["transaction_status"] = df["transaction_status"].astype(str).str.strip().str.upper()
    df.loc[~df["transaction_status"].isin(VALID_STATUSES), "transaction_status"] = "UNKNOWN"
    return df


def _validate_amounts(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])
    df = df[df["amount"] >= 0]
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with negative/invalid amounts.", dropped)
    return df, dropped
