"""
analytics.py
------------
Analytics endpoints, backed by optimized raw SQL (via SQLAlchemy `text()`)
rather than the ORM — for aggregate queries this is both faster and
clearer than building up equivalent ORM expressions.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    AnalyticsSummary,
    ChannelPerformance,
    DailySummary,
    MerchantPerformance,
    TopUser,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary, summary="Overall KPI + daily summary")
def get_summary(
    response: Response,
    payment_method: str | None = Query(None),
    transaction_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    base_where = "WHERE 1=1"
    params = {}
    if payment_method:
        base_where += " AND payment_method = :pm"
        params["pm"] = payment_method
    if transaction_status:
        base_where += " AND transaction_status = :ts"
        params["ts"] = transaction_status

    # Using CASE WHEN instead of FILTER for cross-database compatibility (SQLite/Postgres)
    totals = db.execute(
        text(
            f"""
            SELECT
                COUNT(*)                                            AS total_transactions,
                SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END) AS total_revenue,
                SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END)       AS failed_count,
                SUM(CASE WHEN is_suspicious THEN 1 ELSE 0 END)                       AS suspicious_count
            FROM transactions
            {base_where}
            """
        ),
        params,
    ).mappings().one()

    most_used = db.execute(
        text(
            f"""
            SELECT payment_method
            FROM transactions
            {base_where}
            GROUP BY payment_method
            ORDER BY COUNT(*) DESC, payment_method ASC
            LIMIT 1
            """
        ),
        params,
    ).scalar()

    daily_rows = db.execute(
        text(
            f"""
            SELECT
                DATE(timestamp)                                      AS day,
                COUNT(*)                                             AS total_transactions,
                SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END) AS total_revenue,
                SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END)       AS failed_count
            FROM transactions
            {base_where}
            GROUP BY day
            ORDER BY day DESC
            LIMIT 30
            """
        ),
        params,
    ).mappings().all()

    return AnalyticsSummary(
        total_transactions=totals["total_transactions"] or 0,
        total_revenue=float(totals["total_revenue"] or 0),
        failed_transaction_count=totals["failed_count"] or 0,
        most_used_payment_method=most_used,
        suspicious_transaction_count=totals["suspicious_count"] or 0,
        daily_summary=[
            DailySummary(
                day=str(row["day"]),
                total_transactions=row["total_transactions"],
                total_revenue=float(row["total_revenue"]),
                failed_count=row["failed_count"],
            )
            for row in daily_rows
        ],
    )


@router.get("/top-users", response_model=list[TopUser], summary="Top spending users")
def get_top_users(
    response: Response,
    limit: int = 10,
    payment_method: str | None = Query(None),
    transaction_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    base_where = "WHERE 1=1"
    params = {"limit": limit}
    if payment_method:
        base_where += " AND payment_method = :pm"
        params["pm"] = payment_method
    if transaction_status:
        base_where += " AND transaction_status = :ts"
        params["ts"] = transaction_status

    # If we are filtering by something other than SUCCESS, sort by count 
    # so the "Top Users" chart is still meaningful.
    sort_column = "total_spent" if not transaction_status or transaction_status == "SUCCESS" else "transaction_count"

    rows = db.execute(
        text(
            f"""
            SELECT
                user_id,
                SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END) AS total_spent,
                COUNT(*)                                                              AS transaction_count
            FROM transactions
            {base_where}
            GROUP BY user_id
            ORDER BY {sort_column} DESC
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()

    return [
        TopUser(
            user_id=row["user_id"],
            total_spent=float(row["total_spent"] or 0),
            transaction_count=row["transaction_count"],
        )
        for row in rows
    ]


@router.get(
    "/merchant-performance",
    response_model=list[MerchantPerformance],
    summary="Merchant performance breakdown",
)
def get_merchant_performance(
    response: Response,
    payment_method: str | None = Query(None),
    transaction_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    base_where = "WHERE 1=1"
    params = {}
    if payment_method:
        base_where += " AND payment_method = :pm"
        params["pm"] = payment_method
    if transaction_status:
        base_where += " AND transaction_status = :ts"
        params["ts"] = transaction_status

    rows = db.execute(
        text(
            f"""
            SELECT
                merchant_id,
                SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END) AS total_revenue,
                COUNT(*)                                                              AS transaction_count,
                SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END)        AS failed_count
            FROM transactions
            {base_where}
            GROUP BY merchant_id
            ORDER BY total_revenue DESC, merchant_id ASC
            """
        ),
        params,
    ).mappings().all()

    results = []
    for row in rows:
        success_rate = (
            (row["transaction_count"] - row["failed_count"]) / row["transaction_count"] * 100
            if row["transaction_count"]
            else 0
        )
        results.append(
            MerchantPerformance(
                merchant_id=row["merchant_id"],
                total_revenue=float(row["total_revenue"] or 0),
                transaction_count=row["transaction_count"] or 0,
                failed_count=row["failed_count"] or 0,
                success_rate=round(success_rate, 2),
            )
        )
    return results


@router.get(
    "/channel-performance",
    response_model=list[ChannelPerformance],
    summary="Payment channel performance breakdown",
)
def get_channel_performance(
    response: Response,
    payment_method: str | None = Query(None),
    transaction_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    base_where = "WHERE 1=1"
    params = {}
    if payment_method:
        base_where += " AND payment_method = :pm"
        params["pm"] = payment_method
    if transaction_status:
        base_where += " AND transaction_status = :ts"
        params["ts"] = transaction_status

    rows = db.execute(
        text(
            f"""
            SELECT
                payment_method,
                SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END) AS total_revenue,
                COUNT(*)                                                              AS transaction_count,
                SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END)        AS failed_count
            FROM transactions
            {base_where}
            GROUP BY payment_method
            ORDER BY total_revenue DESC, payment_method ASC
            """
        ),
        params,
    ).mappings().all()

    results = []
    for row in rows:
        success_rate = (
            (row["transaction_count"] - row["failed_count"]) / row["transaction_count"] * 100
            if row["transaction_count"]
            else 0
        )
        results.append(
            ChannelPerformance(
                payment_method=row["payment_method"],
                total_revenue=float(row["total_revenue"] or 0),
                transaction_count=row["transaction_count"] or 0,
                failed_count=row["failed_count"] or 0,
                success_rate=round(success_rate, 2),
            )
        )
    return results
