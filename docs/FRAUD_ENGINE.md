# 🧠 Fraud Engine Logic

The Fraud Detection Engine (FDE) is a rule-based system designed to provide **explainable** risk assessment for every transaction.

## 🛠 Active Rules

### 1. High Amount Threshold (`HIGH_AMOUNT`)
*   **Logic:** `amount > THRESHOLD`
*   **Default:** 50,000 BDT.
*   **Reasoning:** Large transactions are high-risk and often require manual verification in real-world MFS systems.

### 2. Repeat Failures (`REPEAT_FAILURES`)
*   **Logic:** Flags any user who has had $\ge 3$ failed transactions within the current dataset.
*   **Reasoning:** Multiple consecutive failures can indicate a technical issue, a stolen card attempt, or a brute-force attack.

### 3. Duplicate Attempt (`DUPLICATE_ATTEMPT`)
*   **Logic:** Flags transactions with the same `user_id`, `merchant_id`, and `amount` that occur within a 5-minute window.
*   **Reasoning:** This catches accidental "double-taps" by users or duplicate charge requests from merchant integrations.

## 📈 Implementation Details
The engine is implemented using **Pandas vectorization**. Instead of checking each row, we use grouping and time-series shifting to identify patterns across the entire dataset in a single pass.

```python
# Example of Duplicate Sequence Logic
group_cols = ["user_id", "merchant_id", "amount"]
time_diff = sorted_df.groupby(group_cols)["timestamp"].diff()
is_duplicate = time_diff <= pd.Timedelta(minutes=5)
```

## 🎯 Explanability
Every flagged transaction includes a `suspicious_reason` string. This allows dashboard operators to understand exactly why a transaction was marked as risky.
