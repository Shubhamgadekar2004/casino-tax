"""
Player Ledger Page — Individual account summary, game history, and charts.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from models.individual import get_all_individuals, get_individual_summary
from models.transaction import get_individual_ledger
from database.database import execute_query


def render():
    st.title("📒 Player Ledger")
    st.caption("Individual Player Account — Summary, History, and Analytics")

    # ── Select Individual ──────────────────────────────────
    individuals = get_all_individuals()
    selected_pan = st.selectbox(
        "Select Player",
        [i["pan"] for i in individuals],
        format_func=lambda x: f"{x} — {next((i['first_name'] + ' ' + i['last_name'] for i in individuals if i['pan'] == x), '')}",
    )

    if not selected_pan:
        return

    ind = next((i for i in individuals if i["pan"] == selected_pan), None)
    if not ind:
        return

    summary = get_individual_summary(ind["individual_id"])
    ledger = get_individual_ledger(selected_pan)

    if not summary:
        st.warning("No data found for this individual.")
        return

    totals = summary["totals"]
    ledger_summary = ledger["summary"]

    # ── Account Summary KPIs ──────────────────────────────
    st.subheader("💼 Account Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Buy-ins", f"₹{ledger_summary['BUY_IN']:,.2f}")
    c2.metric("Total Winnings", f"₹{ledger_summary['WINNING']:,.2f}")
    c3.metric("Net Game Result", f"₹{ledger['net_result']:+,.2f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Total TDS", f"₹{ledger_summary['TDS']:,.2f}")
    c5.metric("Total Redemptions", f"₹{ledger_summary['REDEMPTION']:,.2f}")
    c6.metric("Games Played", totals["games_played"])

    st.divider()

    # ── Game-wise History ──────────────────────────────────
    st.subheader("🎮 Game-wise History")
    games = summary["games"]
    winnings = {w["game_id"]: w for w in summary.get("winnings", [])}

    game_history = []
    for g in games:
        gid = g["game_id"]
        w = winnings.get(gid, {})
        winning_amt = w.get("gross_winning", 0)
        buy_in = g["buy_in_amount"]
        game_history.append({
            "Game": gid,
            "Date": g["game_date"],
            "Type": g["game_type"],
            "Buy-in": buy_in,
            "Winning": winning_amt,
            "Net": winning_amt - buy_in,
            "Winner?": "✅" if g["is_winner"] else "❌",
            "Shared?": "Yes" if w.get("allocation_method", "") in ("EQUAL_SHARE", "PERCENTAGE_BASED", "FIXED_AMOUNT") else "No",
        })

    if game_history:
        df_hist = pd.DataFrame(game_history)
        df_display = df_hist.copy()
        df_display["Buy-in"] = df_display["Buy-in"].apply(lambda x: f"₹{x:,.0f}")
        df_display["Winning"] = df_display["Winning"].apply(lambda x: f"₹{x:,.0f}")
        df_display["Net"] = df_display["Net"].apply(lambda x: f"₹{x:+,.0f}")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.divider()

    # ── Charts ─────────────────────────────────────────────
    if game_history:
        df_chart = pd.DataFrame(game_history)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Winnings by Game")
            df_win = df_chart[df_chart["Winning"] > 0]
            if not df_win.empty:
                fig1 = px.bar(
                    df_win, x="Game", y="Winning",
                    color="Type",
                    labels={"Winning": "Amount (₹)"},
                )
                fig1.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No winnings to display.")

        with col2:
            st.subheader("📈 Buy-in vs Winnings")
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                name="Buy-in", x=df_chart["Game"], y=df_chart["Buy-in"],
                marker_color="#e63757",
            ))
            fig2.add_trace(go.Bar(
                name="Winning", x=df_chart["Game"], y=df_chart["Winning"],
                marker_color="#00d97e",
            ))
            fig2.update_layout(
                template="plotly_dark", barmode="group", height=300,
            )
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("🗓️ Monthly Activity")
            df_chart["Month"] = pd.to_datetime(df_chart["Date"]).dt.to_period("M").astype(str)
            monthly = df_chart.groupby("Month").agg(
                Games=("Game", "count"),
                Total_Winning=("Winning", "sum"),
            ).reset_index()
            fig3 = px.bar(
                monthly, x="Month", y="Games",
                color="Total_Winning",
                color_continuous_scale="Viridis",
            )
            fig3.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.subheader("🏆 Winning Frequency")
            win_count = len(df_chart[df_chart["Winning"] > 0])
            loss_count = len(df_chart[df_chart["Winning"] == 0])
            fig4 = px.pie(
                names=["Won", "Lost/No Win"],
                values=[win_count, loss_count],
                color_discrete_sequence=["#00d97e", "#e63757"],
                hole=0.4,
            )
            fig4.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig4, use_container_width=True)

    # ── Transaction Ledger ─────────────────────────────────
    with st.expander("📋 Full Transaction Ledger"):
        txns = ledger["transactions"]
        if txns:
            df_txn = pd.DataFrame(txns)
            st.dataframe(df_txn, use_container_width=True, hide_index=True)
