"""
transactions.py
---------------
Endpoints for browsing raw transaction data: all transactions (with
filters), failed transactions, and suspicious transactions.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction
from app.schemas import TransactionOut

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("/", response_model=list[TransactionOut], summary="List transactions with optional filters")
def list_transactions(
    start_date: datetime | None = Query(None, description="Filter: timestamp >= start_date"),
    end_date: datetime | None = Query(None, description="Filter: timestamp <= end_date"),
    payment_method: str | None = Query(None),
    status: str | None = Query(None, alias="transaction_status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Transaction)

    if start_date:
        stmt = stmt.where(Transaction.timestamp >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.timestamp <= end_date)
    if payment_method:
        stmt = stmt.where(Transaction.payment_method == payment_method)
    if status:
        stmt = stmt.where(Transaction.transaction_status == status.upper())

    stmt = stmt.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit)
    return db.execute(stmt).scalars().all()


@router.get("/failed", response_model=list[TransactionOut], summary="Get failed transactions")
def get_failed_transactions(
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Transaction)
        .where(Transaction.transaction_status == "FAILED")
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


@router.get("/suspicious", response_model=list[TransactionOut], summary="Get suspicious transactions")
def get_suspicious_transactions(
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Transaction)
        .where(Transaction.is_suspicious.is_(True))
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()
