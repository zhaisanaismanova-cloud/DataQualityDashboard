
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "data_quality.db"

st.set_page_config(
    page_title="Data Quality Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Data Quality & Sales Dashboard")
st.caption("Monitor data validation, rejected records, and sales performance.")

if not DB_FILE.exists():
    st.error("Database not found. Run clean_data.py and then database.py first.")
    st.stop()

with sqlite3.connect(DB_FILE) as connection:
    cleaned = pd.read_sql_query("SELECT * FROM cleaned_orders", connection)
    rejected = pd.read_sql_query("SELECT * FROM rejected_orders", connection)

total_valid = len(cleaned)
total_rejected = len(rejected)
total_processed = total_valid + total_rejected


col1, col2, col3, col4 = st.columns(4)

col1.metric("Valid Orders", total_valid)
col2.metric("Rejected Orders", total_rejected)
col3.metric(
    "Acceptance Rate",
    f"{total_valid / total_processed * 100:.1f}%" if total_processed else "0%",
)
col4.metric(
    "Total Sales",
    f"${cleaned['order_total'].sum():,.2f}" if not cleaned.empty else "$0.00",
)

st.divider()


left, right = st.columns(2)

with left:
    st.subheader("Sales by Product")
    if not cleaned.empty:
        sales = (
            cleaned.groupby("product", as_index=False)["order_total"]
            .sum()
            .sort_values("order_total", ascending=False)
        )
        st.bar_chart(sales.set_index("product")["order_total"])
    else:
        st.info("No valid sales data available.")

with right:
    st.subheader("Data Quality Overview")
    quality = pd.DataFrame({
        "Status": ["Valid", "Rejected"],
        "Records": [total_valid, total_rejected],
    })
    st.bar_chart(quality.set_index("Status"))



st.divider()
st.subheader("🔎 Validation Issues Breakdown")

if not rejected.empty:
    issue_counts = (
        rejected["rejection_reason"]
        .str.split("; ")
        .explode()
        .value_counts()
        .rename_axis("Issue")
        .reset_index(name="Count")
    )

    st.bar_chart(issue_counts.set_index("Issue")["Count"])

    st.dataframe(
        issue_counts,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success("No validation issues found.")



st.subheader("⚠️ Rejected Orders")
if not rejected.empty:
    st.dataframe(rejected, use_container_width=True, hide_index=True)
else:
    st.success("No rejected orders.")

st.caption("Data source: customer_orders.csv → Python cleaning pipeline → SQLite")
