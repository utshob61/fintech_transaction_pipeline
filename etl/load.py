"""
load.py
-------
Load step of the ETL pipeline.

Takes the cleaned + fraud-flagged DataFrame and writes it into PostgreSQL.

Design notes:
  - users & merchants are derived from the transaction data itself
    (this is a transaction-monitoring system, not a user-management
    system, so we don't require a separate users/merchants feed).
  - Uses INSERT ... ON CONFLICT DO NOTHING so re-running the pipeline
    on overlapping data is idempotent and safe.
"""

import logging

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def load_to_postgres(df: pd.DataFrame, engine: Engine) -> dict:
    """
    Upserts users, merchants, then transactions.

    Returns a dict report: {"users_upserted": int, "merchants_upserted": int,
    "transactions_inserted": int, "transactions_skipped_existing": int}
    """
    report = {}

    with engine.begin() as conn:
        report["users_upserted"] = _upsert_users(conn, df)
        report["merchants_upserted"] = _upsert_merchants(conn, df)
        report.update(_insert_transactions(conn, df))

    logger.info("Load complete: %s", report)
    return report


def _upsert_users(conn, df: pd.DataFrame) -> int:
    user_ids = df["user_id"].dropna().unique().tolist()
    if not user_ids:
        return 0

    stmt = text(
        """
        INSERT INTO users (user_id)
        VALUES (:user_id)
        ON CONFLICT (user_id) DO NOTHING
        """
    )
    conn.execute(stmt, [{"user_id": uid} for uid in user_ids])
    return len(user_ids)


def _upsert_merchants(conn, df: pd.DataFrame) -> int:
    merchant_ids = df["merchant_id"].dropna().unique().tolist()
    if not merchant_ids:
        return 0

    stmt = text(
        """
        INSERT INTO merchants (merchant_id)
        VALUES (:merchant_id)
        ON CONFLICT (merchant_id) DO NOTHING
        """
    )
    conn.execute(stmt, [{"merchant_id": mid} for mid in merchant_ids])
    return len(merchant_ids)


def _insert_transactions(conn, df: pd.DataFrame) -> dict:
    if df.empty:
        return {"transactions_inserted": 0, "transactions_skipped_existing": 0}

    # Count existing rows among this batch's IDs so we can report how many
    # were skipped as already-loaded (idempotent re-runs).
    incoming_ids = df["transaction_id"].tolist()
    existing_result = conn.execute(
        text("SELECT transaction_id FROM transactions WHERE transaction_id = ANY(:ids)"),
        {"ids": incoming_ids},
    )
    existing_ids = {row[0] for row in existing_result}

    stmt = text(
        """
        INSERT INTO transactions (
            transaction_id, user_id, merchant_id, amount,
            payment_method, transaction_status, is_suspicious,
            suspicious_reason, timestamp
        ) VALUES (
            :transaction_id, :user_id, :merchant_id, :amount,
            :payment_method, :transaction_status, :is_suspicious,
            :suspicious_reason, :timestamp
        )
        ON CONFLICT (transaction_id) DO NOTHING
        """
    )

    records = df[
        [
            "transaction_id",
            "user_id",
            "merchant_id",
            "amount",
            "payment_method",
            "transaction_status",
            "is_suspicious",
            "suspicious_reason",
            "timestamp",
        ]
    ].to_dict(orient="records")

    conn.execute(stmt, records)

    inserted = len(incoming_ids) - len(existing_ids)
    return {
        "transactions_inserted": inserted,
        "transactions_skipped_existing": len(existing_ids),
    }
