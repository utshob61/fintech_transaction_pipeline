# 💳 Fintech Transaction Analytics Pipeline

A production-style transaction monitoring & analytics system, modeled on the kind of
pipeline that powers mobile financial services like **bKash** and **Nagad** — built to
demonstrate end-to-end data engineering: ingestion, ETL, fraud flagging, storage, and
a live analytics dashboard.

> Built as a portfolio project for Data Engineering / Fintech internship applications.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [Getting Started (Docker)](#getting-started-docker)
- [Getting Started (Local, no Docker)](#getting-started-local-no-docker)
- [API Documentation](#api-documentation)
- [Dashboard](#dashboard)
- [Fraud Detection Rules](#fraud-detection-rules)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Deployment Guide](#deployment-guide)
- [Sample Data](#sample-data)

---

## Overview

This system ingests raw transaction data (CSV upload or JSON API), runs it through a
modular **Extract → Transform → Load (ETL)** pipeline, flags suspicious activity using
rule-based fraud detection, stores everything in **PostgreSQL**, and exposes both a
**FastAPI** backend (with auto-generated Swagger docs) and a live **Streamlit**
analytics dashboard.

It's fully containerized with Docker Compose — `docker compose up` brings up the
database, API, and dashboard together.

## Architecture

```
                ┌─────────────────┐
   CSV file ──▶ │                 │
                │   ETL Pipeline  │
   JSON API ──▶ │  extract.py     │
                │  transform.py   │──▶ PostgreSQL ──▶ FastAPI ──▶ Streamlit
                │  fraud_detect.py│        ▲              │         Dashboard
                │  load.py        │        │              │       (charts, KPIs,
                └─────────────────┘        │              │      suspicious table)
                                            │              ▼
                                     Indexed tables:   Swagger /docs
                                  users, merchants,
                                     transactions
```

- **ETL** is a standalone Python package (`etl/`) — it doesn't depend on the web
  framework, so it can be run from the CLI, triggered by the API, or scheduled.
- **Backend** (`backend/`) is a thin FastAPI layer over the same ETL package plus
  read-only analytics/transaction query endpoints.
- **Dashboard** (`dashboard/`) only talks to the FastAPI backend over HTTP — it never
  touches the database directly, keeping a clean separation of concerns.

## Tech Stack

| Layer            | Technology                       |
|-------------------|-----------------------------------|
| Backend API       | FastAPI, Pydantic, Uvicorn        |
| Data Processing   | Pandas                            |
| ORM / SQL         | SQLAlchemy 2.0                    |
| Database          | PostgreSQL 15                     |
| Dashboard         | Streamlit, Plotly                 |
| Scheduling        | APScheduler (optional batch jobs) |
| Containerization  | Docker, Docker Compose            |
| Testing           | Pytest                            |

## Project Structure

```
fintech_transaction_pipeline/
│
├── backend/
│   ├── __init__.py
│   └── app/
│       ├── main.py            # FastAPI app + lifespan startup
│       ├── database.py        # SQLAlchemy engine/session
│       ├── models.py          # ORM models (User, Merchant, Transaction)
│       ├── schemas.py         # Pydantic request/response schemas
│       ├── logging_config.py
│       └── routers/
│           ├── upload.py      # POST /api/upload/csv, /api/upload/json
│           ├── transactions.py# GET  /api/transactions, /failed, /suspicious
│           └── analytics.py   # GET  /api/analytics/summary, /top-users, /merchant-performance
│
├── etl/
│   ├── extract.py             # Read CSV / API / JSON records
│   ├── transform.py           # Clean, dedupe, validate, standardize
│   ├── fraud_detection.py     # Rule-based suspicious-transaction flagging
│   ├── load.py                # Upsert into PostgreSQL
│   ├── pipeline.py            # Orchestrates extract→transform→fraud→load
│   └── scheduler.py           # Optional APScheduler batch-job runner
│
├── database/
│   ├── schema.sql              # Tables, PKs, FKs, indexes
│   └── init_db.py              # Applies schema.sql (idempotent)
│
├── dashboard/
│   ├── app.py                  # Streamlit dashboard
│   └── utils.py                # API client helpers
│
├── data/
│   ├── sample_transactions.csv     # 500+ realistic, intentionally-dirty rows
│   └── generate_sample_data.py     # Regenerate the sample dataset
│
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.dashboard
│
├── tests/
│   ├── test_etl.py             # Unit tests for transform + fraud rules
│   └── test_api.py             # FastAPI endpoint tests
│
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── .gitignore
```

## Features

- **Flexible ingestion** — upload a CSV or POST JSON transactions directly to the API.
- **Modular ETL** — `extract.py` / `transform.py` / `load.py`, each independently
  testable and reusable.
- **Data cleaning** — duplicate removal, missing-value handling, timestamp parsing,
  payment-method standardization (`bkash`/`BKASH` → `bKash`), negative-amount rejection.
- **Rule-based fraud detection** — high-value outliers, repeat-failure users, and
  rapid duplicate-attempt patterns, each with a human-readable reason.
- **Analytics** — daily summaries, total revenue, failed-transaction counts, most-used
  payment method, top spenders, and merchant performance — all via optimized SQL.
- **Live dashboard** — KPI cards, revenue/failure trend charts, top users, merchant
  table, suspicious-transaction explorer, and an in-browser CSV uploader that triggers
  the ETL pipeline.
- **Dockerized** — one command (`docker compose up`) runs the database, API, and
  dashboard together.
- **Idempotent loads** — re-running the pipeline on overlapping data won't create
  duplicate rows (`ON CONFLICT DO NOTHING`).

## Getting Started (Docker)

**Prerequisites:** Docker + Docker Compose installed.

```bash
# 1. Clone the repo and enter it
git clone <your-repo-url>
cd fintech_transaction_pipeline

# 2. Copy environment variables
cp .env.example .env

# 3. Build and start everything
docker compose up --build
```

Once running:

| Service     | URL                              |
|-------------|-----------------------------------|
| API (Swagger) | http://localhost:8000/docs       |
| API (ReDoc)   | http://localhost:8000/redoc      |
| Dashboard     | http://localhost:8501            |
| PostgreSQL    | localhost:5432 (see `.env`)       |

**Load the sample data:** open the dashboard sidebar → upload
`data/sample_transactions.csv` → click **Run ETL Pipeline**. Or via curl:

```bash
curl -F "file=@data/sample_transactions.csv" http://localhost:8000/api/upload/csv
```

## Getting Started (Local, no Docker)

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Start a local PostgreSQL instance and update DATABASE_URL in .env
cp .env.example .env
# edit .env -> DATABASE_URL=postgresql://user:pass@localhost:5432/fintech_db

# 4. Initialize the schema
python database/init_db.py

# 5. Run the ETL pipeline once against the sample CSV
python -m etl.pipeline --csv data/sample_transactions.csv

# 6. Start the API (PYTHONPATH needs both the backend dir and project root,
#    since main.py imports both `app.*` and the root-level `etl`/`database` packages)
cd backend
PYTHONPATH=..:. uvicorn app.main:app --reload --port 8000
cd ..

# 7. In another terminal, start the dashboard
streamlit run dashboard/app.py
```

## API Documentation

Interactive Swagger docs are auto-generated at **`/docs`**. Key endpoints:

| Method | Endpoint                          | Description                          |
|--------|------------------------------------|---------------------------------------|
| POST   | `/api/upload/csv`                  | Upload a transactions CSV file        |
| POST   | `/api/upload/json`                 | Ingest transactions as a JSON list    |
| GET    | `/api/transactions/`               | List transactions (filterable)        |
| GET    | `/api/transactions/failed`         | Failed transactions                   |
| GET    | `/api/transactions/suspicious`     | Flagged suspicious transactions       |
| GET    | `/api/analytics/summary`           | KPIs + daily summary                  |
| GET    | `/api/analytics/top-users`         | Top spending users                    |
| GET    | `/api/analytics/merchant-performance` | Revenue/failure rate per merchant  |

## Dashboard

The Streamlit dashboard (`dashboard/app.py`) shows:

- KPI cards: total transactions, total revenue, failed count, suspicious count, top
  payment method
- Daily revenue line chart & daily failed-transaction bar chart
- Top spending users chart
- Merchant performance table (revenue, transaction count, success rate)
- Suspicious transactions table with filters by payment method / status
- A sidebar CSV uploader that runs the ETL pipeline directly from the browser

## Fraud Detection Rules

Implemented in `etl/fraud_detection.py` — simple, explainable, and tunable via `.env`:

1. **High amount** — `amount > FRAUD_HIGH_AMOUNT_THRESHOLD` (default: 50,000)
2. **Repeat failures** — a user with `>= FRAUD_MAX_FAILED_ATTEMPTS` failed transactions
   (default: 3)
3. **Duplicate attempts** — same user + merchant + amount repeated within
   `FRAUD_DUPLICATE_WINDOW_MINUTES` (default: 5 minutes)

Each flagged transaction stores a `suspicious_reason` explaining which rule(s) fired.

## Database Schema

See `database/schema.sql`. Summary:

- **users** (`user_id` PK)
- **merchants** (`merchant_id` PK)
- **transactions** (`transaction_id` PK, `user_id`/`merchant_id` FKs, indexed on
  `timestamp`, `transaction_status`, `payment_method`, and `is_suspicious` for fast
  analytics queries)

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

- `tests/test_etl.py` — pure in-memory tests for cleaning + fraud rules (no DB needed).
- `tests/test_api.py` — FastAPI endpoint tests; DB-dependent tests auto-skip if no
  PostgreSQL instance is reachable, so the suite passes in any environment.

## Deployment Guide

### Render / Railway

1. Push this repo to GitHub.
2. Create a **PostgreSQL** instance on Render/Railway and copy its connection string
   into `DATABASE_URL`.
3. Create a **Web Service** for the backend:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (run from `backend/`)
4. Create a second **Web Service** for the dashboard:
   - Start command: `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
   - Set `DASHBOARD_API_URL` to the backend service's public URL.
5. Add all variables from `.env.example` to each service's environment settings.

### Docker Hub

```bash
docker build -f docker/Dockerfile.backend -t <your-dockerhub-user>/fintech-backend .
docker build -f docker/Dockerfile.dashboard -t <your-dockerhub-user>/fintech-dashboard .
docker push <your-dockerhub-user>/fintech-backend
docker push <your-dockerhub-user>/fintech-dashboard
```

## Sample Data

`data/sample_transactions.csv` contains 500+ generated transactions across 40 users,
15 merchants, and 6 payment methods — **intentionally including** duplicate rows,
missing fields, a negative amount, messy payment-method casing, six high-value
outliers, a user with repeated failures, and a duplicate-attempt sequence — so the
ETL cleaning and fraud-detection logic both have realistic data to demonstrate on.
Regenerate it anytime with:

```bash
python data/generate_sample_data.py
```
