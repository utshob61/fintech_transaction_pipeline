"""
schemas.py
----------
Pydantic schemas used for request validation and response serialization.
Keeping these separate from the SQLAlchemy models (models.py) is a
deliberate clean-architecture choice: API contracts can evolve
independently of the DB schema.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Ingestion ----------

class TransactionIn(BaseModel):
    """A single transaction as received from the JSON ingestion endpoint."""

    transaction_id: str
    user_id: str
    merchant_id: str
    amount: float = Field(ge=0)
    payment_method: str
    transaction_status: str
    timestamp: datetime


class IngestResponse(BaseModel):
    input_rows: int
    output_rows: int
    duplicates_removed: int
    missing_value_rows_dropped: int
    invalid_amount_rows_dropped: int
    users_upserted: int
    merchants_upserted: int
    transactions_inserted: int
    transactions_skipped_existing: int
    suspicious_flagged: int


# ---------- Transactions ----------

class TransactionOut(BaseModel):
    transaction_id: str
    user_id: str
    merchant_id: str
    amount: float
    payment_method: str
    transaction_status: str
    is_suspicious: bool
    suspicious_reason: str | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Analytics ----------

class DailySummary(BaseModel):
    day: str
    total_transactions: int
    total_revenue: float
    failed_count: int


class AnalyticsSummary(BaseModel):
    total_transactions: int
    total_revenue: float
    failed_transaction_count: int
    most_used_payment_method: str | None
    suspicious_transaction_count: int
    daily_summary: list[DailySummary]


class TopUser(BaseModel):
    user_id: str
    total_spent: float
    transaction_count: int


class MerchantPerformance(BaseModel):
    merchant_id: str
    total_revenue: float
    transaction_count: int
    failed_count: int
    success_rate: float
