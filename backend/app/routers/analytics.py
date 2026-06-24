"""
analytics.py
------------
Analytics endpoints, backed by optimized raw SQL (via SQLAlchemy `text()`)
rather than the ORM — for aggregate queries this is both faster and
clearer than building up equivalent ORM expressions.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalyticsSummary, DailySummary, MerchantPerformance, TopUser

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary, summary="Overall KPI + daily summary")
def get_summary(db: Session = Depends(get_db)):
    totals = db.execute(
        text(
            """
            SELECT
                COUNT(*)                                            AS total_transactions,
                COALESCE(SUM(amount) FILTER (WHERE transaction_status = 'SUCCESS'), 0) AS total_revenue,
                COUNT(*) FILTER (WHERE transaction_status = 'FAILED')                  AS failed_count,
                COUNT(*) FILTER (WHERE is_suspicious)                                  AS suspicious_count
            FROM transactions
            """
        )
    ).mappings().one()

    most_used = db.execute(
        text(
            """
            SELECT payment_method
            FROM transactions
            GROUP BY payment_method
            ORDER BY COUNT(*) DESC
            LIMIT 1
            """
        )
    ).scalar()

    daily_rows = db.execute(
        text(
            """
            SELECT
                DATE(timestamp)                                      AS day,
                COUNT(*)                                             AS total_transactions,
                COALESCE(SUM(amount) FILTER (WHERE transaction_status = 'SUCCESS'), 0) AS total_revenue,
                COUNT(*) FILTER (WHERE transaction_status = 'FAILED')                  AS failed_count
            FROM transactions
            GROUP BY DATE(timestamp)
            ORDER BY day DESC
            LIMIT 30
            """
        )
    ).mappings().all()

    return AnalyticsSummary(
        total_transactions=totals["total_transactions"],
        total_revenue=float(totals["total_revenue"]),
        failed_transaction_count=totals["failed_count"],
        most_used_payment_method=most_used,
        suspicious_transaction_count=totals["suspicious_count"],
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
def get_top_users(limit: int = 10, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT
                user_id,
                SUM(amount) FILTER (WHERE transaction_status = 'SUCCESS') AS total_spent,
                COUNT(*)                                                  AS transaction_count
            FROM transactions
            GROUP BY user_id
            ORDER BY total_spent DESC NULLS LAST
            LIMIT :limit
            """
        ),
        {"limit": limit},
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
def get_merchant_performance(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT
                merchant_id,
                COALESCE(SUM(amount) FILTER (WHERE transaction_status = 'SUCCESS'), 0) AS total_revenue,
                COUNT(*)                                                                AS transaction_count,
                COUNT(*) FILTER (WHERE transaction_status = 'FAILED')                   AS failed_count
            FROM transactions
            GROUP BY merchant_id
            ORDER BY total_revenue DESC
            """
        )
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
                total_revenue=float(row["total_revenue"]),
                transaction_count=row["transaction_count"],
                failed_count=row["failed_count"],
                success_rate=round(success_rate, 2),
            )
        )
    return results
