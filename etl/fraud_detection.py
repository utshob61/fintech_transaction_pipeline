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
    pattern). Vectorized for performance on large datasets."""
    
    if df.empty:
        return

    # 1. Sort by grouping columns and timestamp
    group_cols = ["user_id", "merchant_id", "amount"]
    sorted_df = df.sort_values(group_cols + ["timestamp"])
    
    # 2. Calculate time difference between consecutive rows within groups
    time_diff = sorted_df.groupby(group_cols)["timestamp"].diff()
    window = pd.Timedelta(minutes=DUPLICATE_WINDOW_MINUTES)
    
    # 3. Create masks: 
    # mask_b flags the current row if it's too close to the PREVIOUS row
    mask_b = time_diff <= window
    # mask_a flags the current row if it's too close to the NEXT row (by shifting back)
    mask_a = mask_b.shift(-1).fillna(False)
    
    # 4. Map the mask back to the original index
    final_mask_sorted = mask_a | mask_b
    mask_original = final_mask_sorted.reindex(df.index).fillna(False)

    if mask_original.any():
        _append_reason(
            df, mask_original, f"Duplicate attempt within {DUPLICATE_WINDOW_MINUTES} min window"
        )
