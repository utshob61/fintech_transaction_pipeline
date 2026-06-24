"""
app.py
------
Streamlit fintech analytics dashboard.

Run locally with:
    streamlit run dashboard/app.py

Talks to the FastAPI backend (see DASHBOARD_API_URL in .env) for all data —
this file has no direct DB access, keeping a clean separation of concerns.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from utils import API_BASE_URL, fetch_json, format_currency  # noqa: E402

st.set_page_config(
    page_title="Fintech Transaction Analytics",
    page_icon="💳",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Minimal custom styling for a clean, modern fintech look
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .kpi-card {
            background-color: #11161F;
            border: 1px solid #232A36;
            border-radius: 12px;
            padding: 18px 20px;
            text-align: left;
        }
        .kpi-label {
            color: #8A93A6;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }
        .kpi-value {
            color: #F4F6FB;
            font-size: 28px;
            font-weight: 700;
        }
        .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💳 Fintech Transaction Analytics")
st.caption("Real-time transaction monitoring & fraud insight — powered by FastAPI + PostgreSQL")

# ---------------------------------------------------------------------------
# Sidebar: upload + filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📤 Upload Transactions")
    uploaded_file = st.file_uploader("Upload a transactions CSV", type=["csv"])
    if uploaded_file is not None and st.button("Run ETL Pipeline", use_container_width=True):
        with st.spinner("Extracting, cleaning, fraud-flagging, and loading..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                resp = requests.post(f"{API_BASE_URL}/api/upload/csv", files=files, timeout=60)
                resp.raise_for_status()
                st.success("Pipeline completed.")
                st.json(resp.json())
                st.cache_data.clear()
            except requests.exceptions.RequestException as e:
                st.error(f"Upload failed: {e}")

    st.divider()
    st.header("🔎 Filters")
    payment_method_filter = st.selectbox(
        "Payment method", ["All", "bKash", "Nagad", "Rocket", "Card", "Bank Transfer", "Cash"]
    )
    status_filter = st.selectbox("Status", ["All", "SUCCESS", "FAILED", "PENDING"])

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
summary = fetch_json("/api/analytics/summary")

if summary is None:
    st.warning(
        "Couldn't load analytics. Make sure the backend & database are running "
        "(`docker compose up`) and that some data has been uploaded."
    )
    st.stop()

kpi_cols = st.columns(5)
kpis = [
    ("Total Transactions", f"{summary['total_transactions']:,}"),
    ("Total Revenue", format_currency(summary["total_revenue"])),
    ("Failed Transactions", f"{summary['failed_transaction_count']:,}"),
    ("Suspicious Transactions", f"{summary['suspicious_transaction_count']:,}"),
    ("Top Payment Method", summary["most_used_payment_method"] or "—"),
]
for col, (label, value) in zip(kpi_cols, kpis):
    with col:
        st.markdown(
            f"""<div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>""",
            unsafe_allow_html=True,
        )

st.write("")

# ---------------------------------------------------------------------------
# Revenue & transaction trend charts
# ---------------------------------------------------------------------------
daily_df = pd.DataFrame(summary["daily_summary"]).sort_values("day")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈 Daily Revenue")
    if not daily_df.empty:
        fig = px.line(daily_df, x="day", y="total_revenue", markers=True)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet — upload a CSV to get started.")

with chart_col2:
    st.subheader("⚠️ Daily Failed Transactions")
    if not daily_df.empty:
        fig = px.bar(daily_df, x="day", y="failed_count")
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet.")

# ---------------------------------------------------------------------------
# Top users & merchant performance
# ---------------------------------------------------------------------------
top_col, merchant_col = st.columns(2)

with top_col:
    st.subheader("🏆 Top Spending Users")
    top_users = fetch_json("/api/analytics/top-users", params={"limit": 10})
    if top_users:
        tdf = pd.DataFrame(top_users)
        fig = px.bar(tdf, x="user_id", y="total_spent", text_auto=".2s")
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet.")

with merchant_col:
    st.subheader("🏪 Merchant Performance")
    merchants = fetch_json("/api/analytics/merchant-performance")
    if merchants:
        mdf = pd.DataFrame(merchants)
        st.dataframe(
            mdf.rename(
                columns={
                    "merchant_id": "Merchant",
                    "total_revenue": "Revenue",
                    "transaction_count": "Transactions",
                    "failed_count": "Failed",
                    "success_rate": "Success Rate (%)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No data yet.")

# ---------------------------------------------------------------------------
# Suspicious transactions table
# ---------------------------------------------------------------------------
st.subheader("🚨 Suspicious Transactions")
suspicious = fetch_json("/api/transactions/suspicious", params={"limit": 200})

if suspicious:
    sdf = pd.DataFrame(suspicious)

    if payment_method_filter != "All":
        sdf = sdf[sdf["payment_method"] == payment_method_filter]
    if status_filter != "All":
        sdf = sdf[sdf["transaction_status"] == status_filter]

    st.dataframe(
        sdf[
            [
                "transaction_id",
                "user_id",
                "merchant_id",
                "amount",
                "payment_method",
                "transaction_status",
                "suspicious_reason",
                "timestamp",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No suspicious transactions found (or no data loaded yet).")
