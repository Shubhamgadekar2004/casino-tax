"""
ITR Reconciliation Page — Compare casino records with ITR declarations.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from models.reconciliation import (
    get_all_reconciliations, get_reconciliation_by_status,
    get_itr_records,
)
from services.reconciliation_service import (
    reconcile_individual, get_reconciliation_summary,
)
from models.individual import get_all_individuals
from config.settings import RECONCILIATION_STATUSES


def render():
    st.title("📑 ITR Reconciliation")
    st.caption("Casino Records vs ITR Declarations — Mismatch Detection")

    # ── Summary KPIs ───────────────────────────────────────
    recon_summary = get_reconciliation_summary()
    if recon_summary:
        df_sum = pd.DataFrame(recon_summary)
        status_counts = {r["status"]: r["count"] for r in recon_summary}

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("✅ Match", status_counts.get("MATCH", 0))
        c2.metric("🔍 Review", status_counts.get("REVIEW", 0))
        c3.metric("⬇️ Under-Reported", status_counts.get("UNDER-REPORTED", 0))
        c4.metric("🚫 Not-Reported", status_counts.get("NOT-REPORTED", 0))
        c5.metric("⬆️ Over-Reported", status_counts.get("OVER-REPORTED", 0))

    st.divider()

    # ── Tabs ───────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 Reconciliation Table", "🔍 Individual Lookup", "📋 ITR Records"])

    with tab1:
        # ── Filter by Status ──────────────────────────────
        status_filter = st.selectbox(
            "Filter by Status",
            ["ALL"] + RECONCILIATION_STATUSES,
        )

        if status_filter == "ALL":
            recon = get_all_reconciliations()
        else:
            recon = get_reconciliation_by_status(status_filter)

        if recon:
            df = pd.DataFrame(recon)
            display_df = df[[
                "pan", "first_name", "last_name",
                "casino_winnings", "itr_declared_winnings", "difference",
                "tds_deducted", "expected_tax", "reported_tax", "status",
            ]].copy()

            for col in ["casino_winnings", "itr_declared_winnings", "difference",
                        "tds_deducted", "expected_tax", "reported_tax"]:
                display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}")

            display_df.columns = [
                "PAN", "First Name", "Last Name",
                "Casino Winnings", "ITR Declared", "Difference",
                "TDS", "Expected Tax", "Reported Tax", "Status",
            ]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Chart: Casino vs ITR
            df_chart = pd.DataFrame(recon)
            df_chart["name"] = df_chart["first_name"] + " " + df_chart["last_name"]
            df_chart = df_chart[df_chart["casino_winnings"] > 0]

            if not df_chart.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="Casino Winnings", x=df_chart["name"],
                    y=df_chart["casino_winnings"], marker_color="#667eea",
                ))
                fig.add_trace(go.Bar(
                    name="ITR Declared", x=df_chart["name"],
                    y=df_chart["itr_declared_winnings"], marker_color="#00d97e",
                ))
                fig.update_layout(
                    template="plotly_dark", barmode="group", height=400,
                    title="Casino Winnings vs ITR Declaration",
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Status distribution pie
            if recon_summary:
                fig2 = px.pie(
                    df_sum, names="status", values="count",
                    color="status",
                    color_discrete_map={
                        "MATCH": "#00d97e",
                        "REVIEW": "#f6c23e",
                        "UNDER-REPORTED": "#e63757",
                        "NOT-REPORTED": "#e63757",
                        "OVER-REPORTED": "#fd7e14",
                    },
                )
                fig2.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig2, use_container_width=True)

            csv = pd.DataFrame(recon).to_csv(index=False)
            st.download_button("📥 Download Reconciliation CSV", csv, "reconciliation.csv", "text/csv")

    with tab2:
        st.subheader("Individual Reconciliation Lookup")
        individuals = get_all_individuals()
        selected_pan = st.selectbox(
            "Select Individual",
            [i["pan"] for i in individuals],
            format_func=lambda x: f"{x} — {next((i['first_name'] + ' ' + i['last_name'] for i in individuals if i['pan'] == x), '')}",
            key="recon_lookup",
        )

        if selected_pan:
            result = reconcile_individual(selected_pan)
            if result:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Casino Winnings", f"₹{result['casino_winnings']:,.2f}")
                    st.metric("ITR Declared", f"₹{result['itr_declared_winnings']:,.2f}")
                    st.metric("Difference", f"₹{result['difference']:,.2f}")

                with col2:
                    st.metric("TDS Deducted", f"₹{result['tds_deducted']:,.2f}")
                    st.metric("Expected Tax", f"₹{result['expected_tax']:,.2f}")
                    st.metric("Reported Tax", f"₹{result['reported_tax']:,.2f}")

                # Status badge
                status = result["status"]
                color_map = {
                    "MATCH": "🟢", "REVIEW": "🟡",
                    "UNDER-REPORTED": "🔴", "NOT-REPORTED": "🔴",
                    "OVER-REPORTED": "🟠",
                }
                st.markdown(f"### Status: {color_map.get(status, '⚪')} {status}")

    with tab3:
        st.subheader("ITR Records")
        itr = get_itr_records()
        if itr:
            df_itr = pd.DataFrame(itr)
            display_itr = df_itr[[
                "pan", "first_name", "last_name", "assessment_year",
                "casino_winnings_declared", "tax_paid", "tds_claimed",
                "verification_status",
            ]].copy()
            for col in ["casino_winnings_declared", "tax_paid", "tds_claimed"]:
                display_itr[col] = display_itr[col].apply(lambda x: f"₹{x:,.2f}")
            display_itr.columns = [
                "PAN", "Name", "Last Name", "AY",
                "Casino Declared", "Tax Paid", "TDS Claimed", "Status",
            ]
            st.dataframe(display_itr, use_container_width=True, hide_index=True)

            csv = df_itr.to_csv(index=False)
            st.download_button("📥 Download ITR CSV", csv, "itr_records.csv", "text/csv")
