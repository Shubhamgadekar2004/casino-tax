"""
Dashboard Page — KPIs, charts, and overview.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database.database import execute_query
from services.transaction_service import get_dashboard_kpis
from services.game_service import get_game_statistics, get_game_type_distribution
from services.winnings_service import get_winnings_by_individual, get_single_vs_shared_stats
from models.reconciliation import get_risk_distribution, get_all_reconciliations


def render():
    st.title("🏠 Dashboard")
    st.caption("Casino Individual Tax & Accounting — Overview")

    # ── KPI Row ────────────────────────────────────────────
    kpis = get_dashboard_kpis()
    game_stats = get_game_statistics()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Individuals", "20")
    c2.metric("Total Games", game_stats.get("total_games", 0))
    c3.metric("Total Transactions", kpis.get("total_transactions", 0))
    c4.metric("Unique Players", kpis.get("unique_players", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total Winnings", f"₹{kpis.get('total_winnings', 0):,.0f}")
    c6.metric("Total Buy-ins", f"₹{kpis.get('total_buyins', 0):,.0f}")
    c7.metric("Total TDS", f"₹{kpis.get('total_tds', 0):,.0f}")
    c8.metric("Total Prize Pool", f"₹{game_stats.get('total_prize_pool', 0):,.0f}")

    st.divider()

    # ── Chart Row 1 ────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Casino Winnings by Individual")
        win_data = get_winnings_by_individual()
        if win_data:
            df = pd.DataFrame(win_data)
            df["name"] = df["first_name"] + " " + df["last_name"]
            df = df[df["total_winnings"] > 0].sort_values("total_winnings", ascending=True)
            fig = px.bar(
                df, x="total_winnings", y="name", orientation="h",
                color="total_winnings",
                color_continuous_scale="Viridis",
                labels={"total_winnings": "Total Winnings (₹)", "name": "Player"},
            )
            fig.update_layout(
                template="plotly_dark",
                height=400,
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Casino Winnings vs ITR Declaration")
        recon = get_all_reconciliations()
        if recon:
            df_recon = pd.DataFrame(recon)
            df_recon["name"] = df_recon["first_name"] + " " + df_recon["last_name"]
            df_recon = df_recon[df_recon["casino_winnings"] > 0]
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                name="Casino Winnings",
                x=df_recon["name"],
                y=df_recon["casino_winnings"],
                marker_color="#667eea",
            ))
            fig2.add_trace(go.Bar(
                name="ITR Declared",
                x=df_recon["name"],
                y=df_recon["itr_declared_winnings"],
                marker_color="#00d97e",
            ))
            fig2.update_layout(
                template="plotly_dark",
                barmode="group",
                height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Chart Row 2 ────────────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🎯 Single vs Shared Winners")
        shared = get_single_vs_shared_stats()
        if shared:
            df_shared = pd.DataFrame(shared)
            fig3 = px.pie(
                df_shared, names="allocation_method", values="total_amount",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig3.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("⚠️ Risk Distribution")
        risk = get_risk_distribution()
        if risk:
            df_risk = pd.DataFrame(risk)
            colors = {
                "LOW": "#00d97e",
                "MEDIUM": "#f6c23e",
                "HIGH": "#fd7e14",
                "CRITICAL": "#e63757",
            }
            df_risk["color"] = df_risk["risk_level"].map(colors)
            fig4 = px.bar(
                df_risk, x="risk_level", y="count",
                color="risk_level",
                color_discrete_map=colors,
            )
            fig4.update_layout(
                template="plotly_dark",
                height=350,
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig4, use_container_width=True)

    # ── Chart Row 3 ────────────────────────────────────────
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("🎰 Game Type Distribution")
        type_dist = get_game_type_distribution()
        if type_dist:
            df_type = pd.DataFrame(type_dist)
            fig5 = px.pie(
                df_type, names="game_type", values="count",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig5.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.subheader("💰 TDS Collected by Individual")
        tds_data = execute_query(
            """
            SELECT i.first_name || ' ' || i.last_name as name,
                   SUM(t.tds_amount) as total_tds
            FROM tds_records t
            JOIN individuals i ON t.pan = i.pan
            GROUP BY i.individual_id
            ORDER BY total_tds DESC
            LIMIT 10
            """
        )
        if tds_data:
            df_tds = pd.DataFrame(tds_data)
            fig6 = px.bar(
                df_tds, x="name", y="total_tds",
                color="total_tds",
                color_continuous_scale="Reds",
                labels={"total_tds": "TDS (₹)", "name": "Individual"},
            )
            fig6.update_layout(
                template="plotly_dark",
                height=350,
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig6, use_container_width=True)

    # ── Monthly Winnings Chart ─────────────────────────────
    st.subheader("📈 Monthly Winnings Trend")
    monthly = execute_query(
        """
        SELECT strftime('%Y-%m', g.game_date) as month,
               SUM(wa.gross_winning) as total_winnings
        FROM winning_allocations wa
        JOIN games g ON wa.game_id = g.game_id
        GROUP BY month
        ORDER BY month
        """
    )
    if monthly:
        df_monthly = pd.DataFrame(monthly)
        fig7 = px.area(
            df_monthly, x="month", y="total_winnings",
            labels={"total_winnings": "Total Winnings (₹)", "month": "Month"},
            color_discrete_sequence=["#667eea"],
        )
        fig7.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig7, use_container_width=True)
