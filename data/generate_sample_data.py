"""
generate_sample_data.py
------------------------
One-off helper script (not part of the production pipeline) that creates
data/sample_transactions.csv with realistic bKash/Nagad/Rocket-style
transactions — including some intentional dirtiness (duplicates, missing
fields, negative amounts, messy payment-method casing, a few high-value
and rapid-repeat transactions) so the ETL cleaning and fraud-detection
logic both have something real to demonstrate on.

Run with:
    python data/generate_sample_data.py
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_PATH = Path(__file__).parent / "sample_transactions.csv"

USERS = [f"U{1000 + i}" for i in range(40)]
MERCHANTS = [f"M{200 + i}" for i in range(15)]
PAYMENT_METHODS = ["bKash", "bkash", "Nagad", "NAGAD", "Rocket", "Card", "bank transfer", "Cash"]
STATUSES = ["SUCCESS", "FAILED", "PENDING"]
STATUS_WEIGHTS = [0.78, 0.17, 0.05]

start_time = datetime(2026, 5, 1, 8, 0, 0)
rows = []

for i in range(500):
    txn_id = f"TXN{10000 + i}"
    user = random.choice(USERS)
    merchant = random.choice(MERCHANTS)
    amount = round(random.uniform(50, 8000), 2)
    method = random.choice(PAYMENT_METHODS)
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
    ts = start_time + timedelta(minutes=random.randint(0, 60 * 24 * 30))

    rows.append([txn_id, user, merchant, amount, method, status, ts.isoformat()])

# --- Inject some "high amount" outliers (fraud rule 1) ---
for i in range(6):
    txn_id = f"TXNHIGH{i}"
    user = random.choice(USERS)
    merchant = random.choice(MERCHANTS)
    amount = round(random.uniform(60000, 150000), 2)
    ts = start_time + timedelta(minutes=random.randint(0, 60 * 24 * 30))
    rows.append([txn_id, user, merchant, amount, "bKash", "SUCCESS", ts.isoformat()])

# --- Inject a user with repeated failures (fraud rule 2) ---
risky_user = "U9999"
for i in range(5):
    txn_id = f"TXNFAIL{i}"
    merchant = random.choice(MERCHANTS)
    ts = start_time + timedelta(days=2, minutes=i * 3)
    rows.append([txn_id, risky_user, merchant, round(random.uniform(100, 500), 2), "Card", "FAILED", ts.isoformat()])

# --- Inject duplicate-attempt pattern (fraud rule 3): same user/merchant/amount within minutes ---
dup_user, dup_merchant, dup_amount = "U1005", "M205", 2500.00
base_ts = start_time + timedelta(days=5, hours=10)
for i in range(3):
    txn_id = f"TXNDUP{i}"
    ts = base_ts + timedelta(minutes=i * 2)
    rows.append([txn_id, dup_user, dup_merchant, dup_amount, "Nagad", "FAILED" if i < 2 else "SUCCESS", ts.isoformat()])

# --- Inject exact duplicate transaction_id rows (should be removed by transform.py) ---
rows.append(rows[10])
rows.append(rows[55])

# --- Inject rows with missing values ---
rows.append(["TXNMISSING1", "U1010", "M205", "", "bKash", "SUCCESS", (start_time + timedelta(days=1)).isoformat()])
rows.append(["TXNMISSING2", "", "M206", 500, "Card", "SUCCESS", (start_time + timedelta(days=1)).isoformat()])

# --- Inject a negative / invalid amount (should be dropped by transform.py) ---
rows.append(["TXNINVALID1", "U1020", "M210", -250.00, "Cash", "FAILED", (start_time + timedelta(days=3)).isoformat()])

random.shuffle(rows)

with OUTPUT_PATH.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(
        ["transaction_id", "user_id", "merchant_id", "amount", "payment_method", "transaction_status", "timestamp"]
    )
    writer.writerows(rows)

print(f"Generated {len(rows)} rows -> {OUTPUT_PATH}")
