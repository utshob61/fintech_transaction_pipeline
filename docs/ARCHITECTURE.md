# 🏗 Architecture Deep Dive

This document outlines the technical architecture of the Fintech Transaction Pipeline.

## 📡 Data Flow Overview
The pipeline follows a classic **Extract-Transform-Load (ETL)** pattern, optimized for batch processing.

1.  **Ingestion (Extract):** The system accepts raw transaction data via CSV or JSON.
2.  **Vectorized Processing (Transform):**
    *   **Cleaning:** Standardizing timestamps, currency formats, and payment method labels.
    *   **Enrichment:** Running the **Fraud Detection Engine** to add risk flags.
3.  **Database Sync (Load):**
    *   Data is loaded into PostgreSQL using batched `INSERT` statements.
    *   `ON CONFLICT` logic ensures data integrity even with overlapping uploads.
4.  **Consumption:**
    *   FastAPI serves aggregated analytics via REST endpoints.
    *   The frontend uses Plotly.js to render real-time visualizations.

## 🐘 Database Design
The schema is designed for read-heavy analytics. We utilize **Composite Indexes** to ensure that filtering by `payment_method`, `status`, and `timestamp` remains sub-100ms.

### Key Indexes:
*   `idx_transactions_pm_ts`: Optimizes channel-specific performance queries.
*   `idx_transactions_ts_pm_ts`: Optimizes time-series trend analysis.

## 🚀 Performance Optimizations
*   **Vectorization:** By using Pandas, we avoid row-by-row iteration in Python, which is significantly slower for large datasets.
*   **GZip Middleware:** API responses are compressed on-the-fly, reducing bandwidth usage by ~70%.
*   **Idempotency:** The pipeline is designed to be re-run safely, making it resilient to failure.
