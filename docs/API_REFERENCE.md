# 📖 API Reference

Detailed documentation for the Fintech Transaction Pipeline API.

## 📤 Upload & Ingestion

### `POST /api/upload/csv`
Upload a CSV file containing transaction data.
*   **Request:** `multipart/form-data` with `file`.
*   **Response:** JSON report of users, merchants, and transactions processed.

### `DELETE /api/upload/clear`
Clears all data from the database.
*   **Usage:** Primarily for demo resets.
*   **Security:** In production, this would be protected by admin-only scopes.

## 📊 Analytics

### `GET /api/analytics/summary`
Returns top-level KPIs and daily time-series data.
*   **Output:**
    *   `total_volume`: Total processed BDT.
    *   `success_rate`: Percentage of successful transactions.
    *   `daily_trends`: Time-series data for revenue and transaction counts.

### `GET /api/analytics/channel-performance`
Breaks down performance by payment method (bKash, Nagad, etc.).

## 🔍 Transactions

### `GET /api/transactions/suspicious`
Returns a list of all transactions flagged by the **Fraud Detection Engine**.
*   **Filters:** Supports basic filtering and sorting.

### `GET /api/transactions`
Retrieve the most recent transactions with pagination.

---

## 🛠 Developer Notes
*   **Authentication:** Currently open for demo purposes.
*   **CORS:** Enabled for all origins.
*   **Rate Limiting:** Not implemented in this version.
