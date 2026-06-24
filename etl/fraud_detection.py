"""
fraud_detection.py
------------------
Basic RULE-BASED suspicious-transaction detection (not ML — intentionally
simple and explainable, which is what's expected for a portfolio-level
fintech project).

Three rules, each one adds a flag + human-readable reason:

  1. HIGH_AMOUNT       -> amount exceeds a configurable threshold
  2. REPEAT_FAILURES   -> the same user has >= N failed transactions
  3. DUPLICATE_ATTEMPT -> same user+merchant+amount repeated within a
                          short time window (classic "retry" / double-charge
                          pattern)

Flags are stored as boolean `is_suspicious` + a `suspicious_reason` string
so the dashboard/API can explain *why* a transaction was flagged.
"""

import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)

HIGH_AMOUNT_THRESHOLD = float(os.getenv("FRAUD_HIGH_AMOUNT_THRESHOLD", 50_000))
MAX_FAILED_ATTEMPTS = int(os.getenv("FRAUD_MAX_FAILED_ATTEMPTS", 3))
DUPLICATE_WINDOW_MINUTES = int(os.getenv("FRAUD_DUPLICATE_WINDOW_MINUTES", 5))


def flag_suspicious_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds `is_suspicious` (bool) and `suspicious_reason` (str) columns.
    Does not drop or modify any other data.
    """
    df = df.copy()
    df["is_suspicious"] = False
    df["suspicious_reason"] = ""

    _flag_high_amounts(df)
    _flag_repeat_failures(df)
    _flag_duplicate_attempts(df)

    flagged = int(df["is_suspicious"].sum())
    if flagged:
        logger.info("Flagged %d suspicious transactions.", flagged)
    return df


def _append_reason(df: pd.DataFrame, mask: pd.Series, reason: str) -> None:
    df.loc[mask, "is_suspicious"] = True
    existing = df.loc[mask, "suspicious_reason"]
    df.loc[mask, "suspicious_reason"] = existing.apply(
        lambda r: f"{r}; {reason}" if r else reason
    )


def _flag_high_amounts(df: pd.DataFrame) -> None:
    """Rule 1: amount is unusually large."""
    mask = df["amount"] > HIGH_AMOUNT_THRESHOLD
    if mask.any():
        _append_reason(df, mask, f"Amount exceeds {HIGH_AMOUNT_THRESHOLD:,.0f} threshold")


def _flag_repeat_failures(df: pd.DataFrame) -> None:
    """Rule 2: a user with too many FAILED transactions overall."""
    failed_counts = (
        df[df["transaction_status"] == "FAILED"].groupby("user_id").size()
    )
    risky_users = failed_counts[failed_counts >= MAX_FAILED_ATTEMPTS].index

    mask = df["user_id"].isin(risky_users) & (df["transaction_status"] == "FAILED")
    if mask.any():
        _append_reason(df, mask, f">= {MAX_FAILED_ATTEMPTS} failed attempts by this user")


def _flag_duplicate_attempts(df: pd.DataFrame) -> None:
    """Rule 3: same user + merchant + amount repeated within a short window
    (classic accidental double-submit or deliberate retry/duplicate-charge
    pattern)."""
    sorted_df = df.sort_values("timestamp")
    window = pd.Timedelta(minutes=DUPLICATE_WINDOW_MINUTES)

    suspicious_ids = set()
    group_cols = ["user_id", "merchant_id", "amount"]

    for _, group in sorted_df.groupby(group_cols):
        if len(group) < 2:
            continue
        timestamps = group["timestamp"].tolist()
        ids = group["transaction_id"].tolist()
        for i in range(1, len(timestamps)):
            if timestamps[i] - timestamps[i - 1] <= window:
                suspicious_ids.add(ids[i - 1])
                suspicious_ids.add(ids[i])

    if suspicious_ids:
        mask = df["transaction_id"].isin(suspicious_ids)
        _append_reason(
            df, mask, f"Duplicate attempt within {DUPLICATE_WINDOW_MINUTES} min window"
        )
