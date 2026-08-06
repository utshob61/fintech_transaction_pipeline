# 💳 Fintech Transaction Analytics Pipeline 2.0

A high-performance transaction monitoring & analytics system, modeled on industrial-scale pipelines used by mobile financial services like **bKash** and **Nagad**. Built to demonstrate robust data engineering: high-speed ingestion, vectorized ETL, rule-based fraud detection, and a modern analytics dashboard.

> **Live Demo:** [https://fintechtransactionpipeline.vercel.app](https://fintechtransactionpipeline.vercel.app)

---

## 🌟 What's New in 2.0

- **Mobile-First Responsive UI:** A complete redesign using **Tailwind CSS** with a persistent sidebar, glassmorphism effects, and smooth mobile transitions.
- **Performance Overhaul:** 
    - **Vectorized Fraud Detection:** Rule processing scaled for 50,000+ datasets using optimized Pandas operations.
    - **Composite Indexing:** Advanced database indexing for near-instant chart filtering.
    - **GZip Compression:** Up to 70% reduced data payloads for faster mobile browsing.
- **Payment Channel Analytics:** Dedicated performance tracking (revenue, volume, success rates) for bKash, Nagad, Card, Rocket, etc.
- **Unified Vercel Deployment:** Optimized for serverless architecture with a unified static dashboard and FastAPI backend.
- **Robust Data Management:** Added "Clear All" and "Restore Sample Data" features for seamless demo resets.

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Core Features](#features)
- [Getting Started (Docker)](#getting-started-docker)
- [API Documentation](#api-documentation)
- [Fraud Detection Rules](#fraud-detection-rules)
- [Performance Benchmarks](#performance-benchmarks)
- [Deployment Guide](#deployment-guide)

---

## Architecture

```
                ┌─────────────────┐
   CSV file ──▶ │                 │
                │   ETL Pipeline  │
   JSON API ──▶ │  extract.py     │
                │  transform.py   │──▶ PostgreSQL ──▶ FastAPI ──▶ Modern Web
                │  fraud_detect.py│        ▲              │         Dashboard
                │  load.py        │        │              │       (Tailwind,
                └─────────────────┘        │              │       Plotly.js)
                                            │              ▼
                                     Indexed tables:   Swagger /docs
                                  users, merchants,
                                     transactions
```

## Tech Stack

| Layer            | Technology                                     |
|-------------------|------------------------------------------------|
| **Backend API**   | FastAPI, Pydantic, Uvicorn, GZip Middleware    |
| **Frontend**      | Tailwind CSS, Plotly.js, Vanilla JS (ES6+)     |
| **Data Engine**   | Pandas (Vectorized ETL)                        |
| **ORM / SQL**     | SQLAlchemy 2.0 (Dialect Agnostic)              |
| **Database**      | PostgreSQL 15 (Neon/Supabase), SQLite          |
| **Infrastructure**| Docker, Docker Compose, Vercel Serverless      |

## Project Structure

```
fintech_transaction_pipeline/
│
├── backend/
│   └── app/
│       ├── main.py            # Fast startup + auto-seeding logic
│       ├── database.py        # SQLAlchemy engine (Postgres/SQLite fallback)
│       ├── models.py          # Optimized ORM with composite indexes
│       └── routers/           # Analytics, Ingestion, & Transactions
│
├── etl/
│   ├── transform.py           # Standardized data cleaning
│   ├── fraud_detection.py     # High-speed vectorized fraud rules
│   └── load.py                # Batched load logic (5k rows/batch)
│
├── public/                    # Modern Dashboard (Vercel Static)
│   ├── index.html             # Responsive Tailwind UI
│   └── dashboard.js           # Plotly integrations + Cache-Busting
│
├── data/
│   └── sample_transactions.csv     # 500+ generated, intentionally-dirty rows
│
├── docker-compose.yml
├── vercel.json                # Serverless unified config
└── requirements.txt
```

## Features

- **High-Scale Ingestion:** Supports 50,000+ row CSV uploads with vectorized processing and batched database inserts.
- **Smart Data Cleaning:** Automated duplicate removal, missing-value handling, and payment-method standardization.
- **Explainable Fraud Detection:** Real-time flagging for high-value outliers, repeat failures, and duplicate pattern sequences.
- **Interactive Analytics:** Live filtering by channel and status across all KPIs, daily trends, and merchant leaderboards.
- **Mobile Optimized:** sliding sidebar navigation, vanishing toggles, and touch-friendly interactive charts.
- **Idempotent Storage:** Safe to re-run pipeline on overlapping data (`ON CONFLICT DO NOTHING`).

## Getting Started (Docker)

**Prerequisites:** Docker + Docker Compose installed.

```bash
# 1. Clone the repo
git clone https://github.com/utshob61/fintech_transaction_pipeline.git
cd fintech_transaction_pipeline

# 2. Start services
docker compose up --build
```

Access:
- **Web Dashboard:** [http://localhost:8000](http://localhost:8000)
- **API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

## API Documentation

Interactive Swagger docs are auto-generated at **`/docs`**.

| Method | Endpoint                          | Description                          |
|--------|------------------------------------|---------------------------------------|
| POST   | `/api/upload/csv`                  | Upload a transactions CSV file        |
| POST   | `/api/upload/json`                 | Ingest transactions as a JSON list    |
| DELETE | `/api/upload/clear`                | Wipe all data from the database       |
| GET    | `/api/analytics/summary`           | KPIs + daily revenue summary          |
| GET    | `/api/analytics/channel-performance` | Breakdown by payment method        |
| GET    | `/api/transactions/suspicious`     | Flagged suspicious transactions       |

## Fraud Detection Rules

1. **High amount:** `amount > 50,000` (Configurable threshold).
2. **Repeat failures:** Users with `>= 3` failed transactions within the period.
3. **Duplicate attempts:** Same user + merchant + amount within a 5-minute window.

## Deployment Guide

### Vercel (Unified Deployment)
The project is optimized for Vercel Serverless.

1. Connect repo to Vercel.
2. Add `DATABASE_URL` (Neon/Supabase) to Environment Variables for persistence.
3. Deploy!

> **Note:** If no `DATABASE_URL` is provided, the app uses an in-memory SQLite database that auto-seeds with sample data on cold start.

## Performance Benchmarks
- **Ingestion:** 50,000 transactions processed and indexed in < 5 seconds.
- **Analytics:** Complex aggregates calculated in < 100ms via optimized composite indexes.
- **Payload:** GZip compressed responses ensure < 50KB transfer for large table data.
