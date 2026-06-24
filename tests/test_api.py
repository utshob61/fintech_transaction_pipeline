"""
test_api.py
-----------
Basic API tests using FastAPI's TestClient.

Note: the health check test requires no database. The other tests are
written to run against a real Postgres instance (e.g. inside CI with a
postgres service container, or locally after `docker compose up db`) —
set DATABASE_URL accordingly before running them. They're skipped
automatically if the DB isn't reachable, so `pytest` still passes in a
plain sandbox with no database running.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import DATABASE_URL  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def _database_is_reachable() -> bool:
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect():
            return True
    except OperationalError:
        return False


DB_AVAILABLE = _database_is_reachable()


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.skipif(not DB_AVAILABLE, reason="No database available in this environment.")
def test_analytics_summary_returns_expected_shape():
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    body = response.json()
    assert "total_transactions" in body
    assert "daily_summary" in body


@pytest.mark.skipif(not DB_AVAILABLE, reason="No database available in this environment.")
def test_suspicious_transactions_endpoint():
    response = client.get("/api/transactions/suspicious")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.skipif(not DB_AVAILABLE, reason="No database available in this environment.")
def test_upload_rejects_non_csv_file():
    response = client.post(
        "/api/upload/csv",
        files={"file": ("not_a_csv.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
