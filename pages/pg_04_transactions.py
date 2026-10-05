"""
Transactions Page — Immutable ledger view with filters and summaries.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from models.transaction import (
    get_all_transactions, get_transactions_by_pan,
    get_transactions_by_type, get_transaction_summary,
)
from models.individual import get_all_individuals
from config.settings import TRANSACTION_TYPES


def render():
    st.title("💳 Transactions")
    st.caption("Immutable Transaction Ledger — All Casino Operations")

    # ── Summary ────────────────────────────────────────────
    summary = get_transaction_summary()
    if summary:
        df_sum = pd.DataFrame(summary)
        c1, c2, c3, c4 = st.columns(4)
        total_txn = df_sum["count"].sum()
        total_amount = df_sum["total_amount"].sum()
        c1.metric("Total Transactions", f"{total_txn:,}")
        c2.metric("Total Value", f"₹{total_amount:,.0f}")
        credits = df_sum[df_sum["credit_debit"] == "CREDIT"]["total_amount"].sum()
        debits = df_sum[df_sum["credit_debit"] == "DEBIT"]["total_amount"].sum()
        c3.metric("Total Credits", f"₹{credits:,.0f}")
        c4.metric("Total Debits", f"₹{debits:,.0f}")

    st.divider()

    # ── Filters ────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        txn_type_filter = st.selectbox(
            "Transaction Type",
            ["ALL"] + TRANSACTION_TYPES,
        )

    with col2:
        individuals = get_all_individuals()
        pan_options = ["ALL"] + [i["pan"] for i in individuals]
        pan_filter = st.selectbox(
            "PAN",
            pan_options,
            format_func=lambda x: f"{x}" if x == "ALL" else f"{x} — {next((i['first_name'] + ' ' + i['last_name'] for i in individuals if i['pan'] == x), '')}",
        )

    with col3:
        credit_debit = st.selectbox("Credit/Debit", ["ALL", "CREDIT", "DEBIT"])

    # ── Fetch Data ─────────────────────────────────────────
    if pan_filter != "ALL":
        transactions = get_transactions_by_pan(pan_filter)
    elif txn_type_filter != "ALL":
        transactions = get_transactions_by_type(txn_type_filter)
    else:
        transactions = get_all_transactions()

    if not transactions:
        st.info("No transactions found with the selected filters.")
        return

    df = pd.DataFrame(transactions)

    # Apply credit/debit filter
    if credit_debit != "ALL":
        df = df[df["credit_debit"] == credit_debit]

    # Apply type filter on top of PAN filter
    if txn_type_filter != "ALL" and pan_filter != "ALL":
        df = df[df["transaction_type"] == txn_type_filter]

    st.markdown(f"**Showing {len(df)} transactions**")

    # ── Data Table ─────────────────────────────────────────
    display_df = df[[
        "transaction_id", "pan", "game_id", "transaction_date",
        "transaction_type", "amount", "credit_debit", "payment_method",
    ]].copy()
    display_df["amount"] = display_df["amount"].apply(lambda x: f"₹{x:,.2f}")
    display_df.columns = [
        "Txn ID", "PAN", "Game", "Date",
        "Type", "Amount", "Cr/Dr", "Payment",
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False)
    st.download_button("📥 Download Transactions CSV", csv, "transactions.csv", "text/csv")

    st.divider()

    # ── Charts ─────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Transaction Type Distribution")
        if summary:
            fig = px.bar(
                df_sum, x="transaction_type", y="total_amount",
                color="credit_debit",
                barmode="group",
                color_discrete_map={"CREDIT": "#00d97e", "DEBIT": "#e63757"},
                labels={"total_amount": "Amount (₹)", "transaction_type": "Type"},
            )
            fig.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Payment Method Distribution")
        payment_data = df[df["payment_method"].notna() & (df["payment_method"] != "SYSTEM")]
        if not payment_data.empty:
            fig2 = px.pie(
                payment_data, names="payment_method",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig2.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig2, use_container_width=True)
