# 💳 Fintech Transaction Pipeline v2.0

A high-performance transaction monitoring & analytics system, modeled on industrial-scale pipelines used by mobile financial services (MFS) like **bKash** and **Nagad**. Designed for extreme speed, vectorized data processing, and real-time fraud flagging.

> **Live Demo:** [https://fintechtransactionpipeline.vercel.app](https://fintechtransactionpipeline.vercel.app)
> **API Docs:** [https://fintechtransactionpipeline.vercel.app/docs](https://fintechtransactionpipeline.vercel.app/docs)
> **GitHub Repo:** [https://github.com/utshob61/fintech_transaction_pipeline](https://github.com/utshob61/fintech_transaction_pipeline)

---

## 📌 Table of Contents
- [✨ About The Project](#-about-the-project)
- [🧠 Intelligence Engines](#-intelligence-engines)
- [🛠 Tech Stack](#-tech-stack)
- [📂 Project Structure](#-project-structure)
- [🚀 Getting Started](#-getting-started)
- [🎨 Style Guide](#-style-guide)
- [🛡 Security & Integrity](#-security--integrity)
- [📚 Extended Documentation](#-extended-documentation)
- [📈 Roadmap](#-roadmap)
- [📖 API Documentation](#-api-documentation)

---

## ✨ About The Project
The **Fintech Transaction Pipeline** is a robust ETL (Extract, Transform, Load) engine built to handle the complexities of mobile financial transactions. In the MFS ecosystem, data arrives in massive batches and requires instant cleaning, standardization, and risk assessment.

**Key Highlights:**
*   **Production-Grade Ingestion:** Optimized for 50,000+ row CSV batch uploads.
*   **Vectorized ETL:** Leverages NumPy/Pandas for O(n) transformation performance.
*   **Fraud Flagging:** Real-time rule-based engine to identify suspicious patterns.
*   **MFS-Style Dashboard:** A high-fidelity analytics interface with glassmorphism design.

---

## 🧠 Intelligence Engines
The core of the pipeline lies in its ability to derive meaning from raw transaction logs.

### 🛡 Fraud Detection Engine (FDE)
A deterministic, rule-based engine that evaluates every transaction against three primary risk vectors:
1.  **High-Value Outliers:** Flags transactions exceeding a configurable threshold (Default: 50,000 BDT).
2.  **Velocity/Repeat Failures:** Identifies users with $\ge 3$ failed transactions in a single window, suggesting potential brute-force or system issues.
3.  **Duplicate Sequence Logic:** Detects identical (User + Merchant + Amount) pairs occurring within a 5-minute "retry" window.

### 📊 Performance Analytics Engine
Calculates high-level KPIs and daily trends using optimized SQL aggregates:
*   **Success Rate (SR):** Percentage of successful vs. failed transactions.
*   **Channel Volume:** Breakdown of volume by bKash, Nagad, Card, and Rocket.
*   **Revenue Impact:** Real-time calculation of total processed volume.

---

## 🛠 Tech Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Backend** | FastAPI / Python 3.12 | High-concurrency API layer |
| **Data Engine** | Pandas / NumPy | Vectorized ETL & cleaning |
| **Database** | PostgreSQL 15 | Relational storage with composite indexing |
| **ORM** | SQLAlchemy 2.0 | Type-safe database interactions |
| **Frontend** | Tailwind CSS / Plotly.js | Modern dashboard & data viz |
| **Infra** | Docker / Vercel | Containerization & Serverless delivery |

---

## 📂 Project Structure
```text
fintech_transaction_pipeline/
├── backend/app/
│   ├── main.py            # API entry point & lifespan logic
│   ├── models.py          # SQLAlchemy schemas with composite indexes
│   └── routers/           # Domain-driven API modules
├── etl/
│   ├── transform.py       # Vectorized data cleaning logic
│   ├── fraud_detection.py # Rule-based flagging engine
│   └── load.py            # Batched Postgres loader (5k/batch)
├── public/                # Static frontend assets
│   ├── index.html         # Tailwind-powered dashboard
│   └── dashboard.js       # Chart logic & API integration
├── docker/                # Deployment configurations
└── data/                  # Sample transaction datasets
```

---

## 🚀 Getting Started

### 🐳 Docker (Quickest)
```bash
# Clone the repository
git clone https://github.com/utshob61/fintech_transaction_pipeline.git
cd fintech_transaction_pipeline

# Spin up the stack
docker compose up --build
```

### 🐍 Local Development
1.  **Environment:** Create a `.env` file based on `.env.example`.
2.  **Install:** `pip install -r requirements.txt`.
3.  **Run:** `uvicorn backend.app.main:app --reload --port 8000`.

---

## 🎨 Style Guide
The project adheres to a "Modern Fintech" aesthetic, prioritizing clarity and data density.

*   **Typography:** Inter (Primary), JetBrains Mono (Data/Numbers).
*   **Design Tokens:**
    *   **Success Green:** `#10b981`
    *   **Failure Red:** `#ef4444`
    *   **MFS Branding:** Custom color accents for bKash (Pink) and Nagad (Orange).
*   **Visual Philosophy:** Glassmorphism cards, persistent sidebars, and responsive toggles.

---

## 🛡 Security & Integrity
*   **Idempotent Loading:** Uses `ON CONFLICT DO NOTHING` to ensure overlapping data batches don't create duplicates.
*   **Data Isolation:** Strict typing via Pydantic ensures only valid transaction schemas enter the pipeline.
*   **GZip Compression:** All API responses are compressed to minimize data transit costs and improve load times.

---

## 📚 Extended Documentation
For a deeper dive into the architecture and engines:
*   [Architecture Deep Dive](./docs/ARCHITECTURE.md)
*   [Fraud Engine Logic](./docs/FRAUD_ENGINE.md)
*   [API Reference](./docs/API_REFERENCE.md)

---

## 📈 Roadmap
- [ ] ML-based anomaly detection (Isolation Forest).
- [ ] Real-time WebSocket updates for the dashboard.
- [ ] Exportable PDF/Excel merchant reports.
- [ ] Multi-tenant isolation for different merchants.

---

## 📖 API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload/csv` | Bulk ingest transactions from CSV |
| `DELETE` | `/api/upload/clear` | Purge all transaction data (Demo use) |
| `GET` | `/api/analytics/summary` | Fetch top-level KPIs and trends |
| `GET` | `/api/analytics/channel` | Payment channel performance breakdown |
| `GET` | `/api/transactions/suspicious` | List all flagged fraudulent transactions |

---

**Proudly built for the Bangladesh Fintech Ecosystem.**
