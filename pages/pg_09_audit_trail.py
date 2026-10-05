"""
Audit Trail Page — Immutable log of system actions and compliance modifications.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from services.audit_service import (
    get_recent_logs,
    get_audit_summary,
    get_logs_by_entity,
    get_logs_by_user,
)


def render():
    st.title("🔍 Compliance Audit Trail")
    st.caption("Immutable system audit logs tracking entity modifications, tax calculations, and administrative actions.")

    # ── KPI Summary Cards ────────────────────────────────────
    summary = get_audit_summary()
    if summary and len(summary) > 0:
        s = summary[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Audit Entries", s.get("total_entries", 0))
        c2.metric("Unique Operators", s.get("unique_users", 0))
        c3.metric("Entities Tracked", s.get("unique_entities", 0))
        c4.metric("Action Types", s.get("unique_actions", 0))

    st.divider()

    # ── Filters & Search ──────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        entity_filter = st.selectbox(
            "Filter by Entity",
            ["All Entities", "INDIVIDUAL", "GAME", "TRANSACTION", "RECONCILIATION", "TAX_RULE", "RISK_ENGINE"],
        )
    with col2:
        user_filter = st.selectbox(
            "Filter by Operator",
            ["All Operators", "SYSTEM_SEED", "ADMIN", "TAX_ENGINE", "AUDITOR"],
        )
    with col3:
        search_query = st.text_input("Search Description / ID", placeholder="e.g. IND-001 or TDS")

    # Fetch logs
    logs = get_recent_logs(limit=200)
    df_logs = pd.DataFrame(logs)

    if not df_logs.empty:
        # Apply filters
        if entity_filter != "All Entities":
            df_logs = df_logs[df_logs["entity"] == entity_filter]
        if user_filter != "All Operators":
            df_logs = df_logs[df_logs["user_id"] == user_filter]
        if search_query:
            q = search_query.lower()
            df_logs = df_logs[
                df_logs["description"].str.lower().str.contains(q, na=False)
                | df_logs["audit_id"].str.lower().str.contains(q, na=False)
                | df_logs["entity_id"].str.lower().str.contains(q, na=False)
            ]

        # Chart: Activity Timeline
        st.subheader("📈 Audit Event Volume by Entity")
        chart_df = df_logs.groupby(["entity", "action"]).size().reset_index(name="count")
        fig = px.bar(
            chart_df,
            x="entity",
            y="count",
            color="action",
            barmode="stack",
            title="Audit Log Breakdown by Entity & Action",
            template="plotly_dark",
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Log Dataframe
        st.subheader(f"📋 Audit Log Entries ({len(df_logs)})")

        display_cols = ["audit_id", "timestamp", "user_id", "action", "entity", "entity_id", "description"]
        st.dataframe(
            df_logs[display_cols],
            use_container_width=True,
            hide_index=True,
        )

        # Detail Inspector
        st.subheader("🔎 Log Entry Detail Inspector")
        selected_audit_id = st.selectbox("Select Log ID to inspect:", df_logs["audit_id"].tolist())

        if selected_audit_id:
            row = df_logs[df_logs["audit_id"] == selected_audit_id].iloc[0]
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Audit ID:** `{row['audit_id']}`")
                st.markdown(f"**Timestamp:** `{row['timestamp']}`")
                st.markdown(f"**Operator:** `{row['user_id']}`")
                st.markdown(f"**IP Address:** `{row.get('ip_address', 'N/A')}`")
            with col_b:
                st.markdown(f"**Action:** `{row['action']}`")
                st.markdown(f"**Entity:** `{row['entity']}` (ID: `{row.get('entity_id', 'N/A')}`)")
                st.markdown(f"**Description:** {row.get('description', 'N/A')}")

            with st.expander("Show Value Changes (Old vs New)", expanded=True):
                c_old, c_new = st.columns(2)
                with c_old:
                    st.caption("Old Value")
                    st.code(row.get("old_value") or "None / Initial State")
                with c_new:
                    st.caption("New Value")
                    st.code(row.get("new_value") or "None / Unchanged")
    else:
        st.info("No audit logs found matching criteria.")
