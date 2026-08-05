# 💳 Fintech Transaction Analytics Pipeline 2.0

A production-style transaction monitoring & analytics system, modeled on the kind of
pipeline that powers mobile financial services like **bKash** and **Nagad** — built to
demonstrate end-to-end data engineering: ingestion, ETL, fraud flagging, storage, and
a high-performance analytics dashboard.

> **Live Demo:** [https://fintechtransactionpipeline.vercel.app](https://fintechtransactionpipeline.vercel.app)

---

## 🌟 What's New in 2.0

- **Responsive UI:** A complete redesign using **Tailwind CSS** with glassmorphism and dark-mode optimization.
- **Payment Channel Analytics:** Dedicated breakdown of revenue, volume, and success rates for every payment method (bKash, Nagad, Card, etc.).
- **Vercel Native:** Optimized for serverless deployment with a unified static dashboard and FastAPI backend.
- **Auto-Seeding:** Fallback in-memory database now automatically seeds with sample data for an instant demo experience.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [Getting Started (Docker)](#getting-started-docker)
- [API Documentation](#api-documentation)
- [Fraud Detection Rules](#fraud-detection-rules)
- [Deployment Guide](#deployment-guide)

---

## Overview

This system ingests raw transaction data (CSV upload or JSON API), runs it through a
modular **Extract → Transform → Load (ETL)** pipeline, flags suspicious activity using
rule-based fraud detection, stores everything in **PostgreSQL**, and exposes both a
**FastAPI** backend and a responsive **Web Dashboard**.

It's fully containerized with Docker Compose — `docker compose up` brings up the
database, API, and legacy Streamlit dashboard together.

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
| **Backend API**   | FastAPI, Pydantic, Uvicorn                     |
| **Frontend**      | Tailwind CSS, Plotly.js, Vanilla JS (ES6+)     |
| **Data Engine**   | Pandas                                         |
| **ORM / SQL**     | SQLAlchemy 2.0                                 |
| **Database**      | PostgreSQL 15 (Production), SQLite (Fallback)  |
| **Container**     | Docker, Docker Compose                         |
| **Testing**       | Pytest                                         |

## Project Structure

```
fintech_transaction_pipeline/
│
├── backend/
│   └── app/
│       ├── main.py            # FastAPI app + auto-seeding logic
│       ├── database.py        # SQLAlchemy engine/session (with fallback)
│       ├── models.py          # ORM models (Postgres & SQLite compatible)
│       └── routers/           # upload, transactions, analytics
│
├── etl/
│   ├── transform.py           # Clean, dedupe, validate, standardize
│   ├── fraud_detection.py     # Rule-based suspicious-transaction flagging
│   └── load.py                # Dialect-agnostic batch loading (Postgres/SQLite)
│
├── public/                    # 🆕 Modern Dashboard Files
│   ├── index.html             # Responsive Tailwind UI
│   └── dashboard.js           # Plotly.js integrations & API client
│
├── data/
│   └── sample_transactions.csv     # 500+ generated, intentionally-dirty rows
│
├── docker-compose.yml
├── vercel.json                # Vercel deployment configuration
└── requirements.txt
```

## Features

- **Flexible ingestion** — Upload a CSV or POST JSON transactions directly to the API.
- **Data cleaning** — Duplicate removal, missing-value handling, payment-method standardization (`bkash` → `bKash`), and invalid amount rejection.
- **Fraud detection** — Rule-based flagging for high-value outliers, repeat-failure users, and rapid duplicate patterns.
- **Advanced Analytics** — Daily revenue trends, merchant performance, and **Payment Channel breakdowns**.
- **Modern Dashboard** — KPI cards, interactive Plotly charts, and a real-time suspicious activity log.
- **Idempotent loads** — Safe to re-run pipeline on overlapping data (`ON CONFLICT DO NOTHING`).

## Getting Started (Docker)

**Prerequisites:** Docker + Docker Compose installed.

```bash
# 1. Clone the repo
git clone https://github.com/utshob61/fintech_transaction_pipeline.git
cd fintech_transaction_pipeline

# 2. Copy environment variables
cp .env.example .env

# 3. Build and start everything
docker compose up --build
```

Once running:
- **API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Web Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Legacy Dashboard:** [http://localhost:8501](http://localhost:8501) (Streamlit)

## API Documentation

Interactive Swagger docs are auto-generated at **`/docs`**.

| Method | Endpoint                          | Description                          |
|--------|------------------------------------|---------------------------------------|
| POST   | `/api/upload/csv`                  | Upload a transactions CSV file        |
| POST   | `/api/upload/json`                 | Ingest transactions as a JSON list    |
| GET    | `/api/analytics/summary`           | KPIs + daily summary                  |
| GET    | `/api/analytics/channel-performance` | Breakdown by payment method        |
| GET    | `/api/transactions/suspicious`     | Flagged suspicious transactions       |

## Fraud Detection Rules

Implemented in `etl/fraud_detection.py`:
1. **High amount** — `amount > 50,000` (tunable)
2. **Repeat failures** — Users with `>= 3` failed transactions.
3. **Duplicate attempts** — Same user + merchant + amount within a 5-minute window.

## Deployment Guide

### Vercel (Unified Deployment)
The project is pre-configured for Vercel. It hosts the FastAPI backend as serverless functions and serves the `public/` folder as a static site.

1. Connect this repo to Vercel.
2. (Optional) Set `DATABASE_URL` to a remote Postgres (Supabase/Neon).
3. Deploy!

> **Note:** If no `DATABASE_URL` is provided, Vercel will use an in-memory SQLite database that auto-seeds with sample data for demonstration.

## Sample Data
`data/sample_transactions.csv` contains 500+ generated transactions designed to test the ETL pipeline's cleaning and fraud-detection capabilities. Regenerate it with:
```bash
python data/generate_sample_data.py
```
