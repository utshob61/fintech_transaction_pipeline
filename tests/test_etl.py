"""
test_etl.py
-----------
Unit tests for the ETL transform + fraud detection logic.
Pure pandas/in-memory — no database required, so these run anywhere
(including CI) with just `pytest`.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.fraud_detection import flag_suspicious_transactions
from etl.transform import clean_transactions


def make_df(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "transaction_id",
            "user_id",
            "merchant_id",
            "amount",
            "payment_method",
            "transaction_status",
            "timestamp",
        ],
    )


def test_removes_duplicate_transaction_ids():
    df = make_df(
        [
            ["T1", "U1", "M1", 100, "bkash", "SUCCESS", "2026-01-01 10:00:00"],
            ["T1", "U1", "M1", 100, "bkash", "SUCCESS", "2026-01-01 10:00:00"],
        ]
    )
    clean_df, report = clean_transactions(df)
    assert len(clean_df) == 1
    assert report["duplicates_removed"] == 1


def test_drops_rows_missing_critical_fields():
    df = make_df(
        [
            ["T1", "U1", "M1", 100, "bkash", "SUCCESS", "2026-01-01 10:00:00"],
            ["T2", None, "M1", 100, "bkash", "SUCCESS", "2026-01-01 10:00:00"],
        ]
    )
    clean_df, report = clean_transactions(df)
    assert len(clean_df) == 1
    assert report["missing_value_rows_dropped"] == 1


def test_drops_negative_amounts():
    df = make_df(
        [
            ["T1", "U1", "M1", 100, "bkash", "SUCCESS", "2026-01-01 10:00:00"],
            ["T2", "U1", "M1", -50, "bkash", "SUCCESS", "2026-01-01 10:00:00"],
        ]
    )
    clean_df, report = clean_transactions(df)
    assert len(clean_df) == 1
    assert report["invalid_amount_rows_dropped"] == 1


def test_standardizes_payment_method_casing():
    df = make_df(
        [
            ["T1", "U1", "M1", 100, "bkash", "SUCCESS", "2026-01-01 10:00:00"],
            ["T2", "U2", "M1", 100, "BKASH", "SUCCESS", "2026-01-01 10:00:00"],
        ]
    )
    clean_df, _ = clean_transactions(df)
    assert set(clean_df["payment_method"]) == {"bKash"}


def test_flags_high_amount_transactions():
    # Default threshold is 50,000 — use an amount well above it so the test
    # doesn't depend on mutating shared module-level config.
    df = make_df(
        [
            ["T1", "U1", "M1", 200000, "bKash", "SUCCESS", "2026-01-01 10:00:00"],
        ]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    flagged = flag_suspicious_transactions(df)
    assert bool(flagged["is_suspicious"].iloc[0]) is True
    assert "Amount exceeds" in flagged["suspicious_reason"].iloc[0]


def test_flags_repeat_failures():
    rows = [
        [f"T{i}", "U1", "M1", 100, "bKash", "FAILED", f"2026-01-01 10:0{i}:00"]
        for i in range(4)
    ]
    df = make_df(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    flagged = flag_suspicious_transactions(df)
    assert flagged["is_suspicious"].all()


def test_flags_duplicate_attempts_within_window():
    df = make_df(
        [
            ["T1", "U1", "M1", 500, "Nagad", "FAILED", "2026-01-01 10:00:00"],
            ["T2", "U1", "M1", 500, "Nagad", "SUCCESS", "2026-01-01 10:02:00"],
        ]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    flagged = flag_suspicious_transactions(df)
    assert flagged["is_suspicious"].all()
