"""Python-only analytics assistant endpoint.

The endpoint sends only aggregate transaction data to the configured OpenAI
model.  When no API key is available it still provides an on-device summary,
so the dashboard remains useful during local development.
"""

import os
from typing import Any

import requests
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["AI Assistant"])


def get_context(db: Session) -> dict[str, Any]:
    totals = db.execute(text("""
        SELECT COUNT(*) AS transactions,
               COALESCE(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END), 0) AS revenue,
               COALESCE(SUM(CASE WHEN transaction_status = 'FAILED' THEN 1 ELSE 0 END), 0) AS failures,
               COALESCE(SUM(CASE WHEN is_suspicious THEN 1 ELSE 0 END), 0) AS suspicious
        FROM transactions
    """)).mappings().one()
    channels = db.execute(text("""
        SELECT payment_method, COUNT(*) AS transactions,
               COALESCE(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END), 0) AS revenue
        FROM transactions GROUP BY payment_method ORDER BY revenue DESC LIMIT 5
    """)).mappings().all()
    return {"totals": dict(totals), "top_channels": [dict(row) for row in channels]}


def local_reply(context: dict[str, Any]) -> str:
    totals = context["totals"]
    count = totals["transactions"]
    if not count:
        return "There is no transaction data yet. Upload a CSV, then ask me about revenue, failed payments, or fraud alerts."
    failure_rate = totals["failures"] / count * 100
    channels = context["top_channels"]
    channel_note = f" Top channel by successful revenue: {channels[0]['payment_method']}." if channels else ""
    return (
        f"Current portfolio: {count:,} transactions, ৳{float(totals['revenue']):,.2f} in successful revenue, "
        f"{totals['failures']:,} failed payments ({failure_rate:.1f}%), and {totals['suspicious']:,} flagged transactions."
        f"{channel_note} Add OPENAI_API_KEY to get natural-language analysis of your questions."
    )


@router.post("", response_model=ChatResponse, summary="Ask the transaction analytics assistant")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    context = get_context(db)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ChatResponse(reply=local_reply(context), mode="local-insights")

    prompt = (
        "You are a concise fintech transaction analytics assistant. Answer only from the aggregate "
        "data below; do not invent values or give financial advice. Use BDT (৳) for money. "
        f"Aggregate data: {context}\nUser question: {request.message}"
    )
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "input": prompt},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        reply = payload.get("output_text")
        if not reply:
            raise ValueError("The model returned no text")
        return ChatResponse(reply=reply, mode="openai")
    except (requests.RequestException, ValueError):
        return ChatResponse(reply=local_reply(context), mode="local-insights")
