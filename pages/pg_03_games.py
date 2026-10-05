"""
Games Page — Game Explorer with participant tables and winning allocations.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from models.game import get_all_games, get_game_summary
from services.game_service import (
    get_game_explorer_data, get_game_statistics,
    get_game_type_distribution, validate_winning_allocation,
)


def render():
    st.title("🎰 Games")
    st.caption("20 Games — Single Winner, Shared Winners, No Winner Scenarios")

    # ── KPIs ───────────────────────────────────────────────
    stats = get_game_statistics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Games", stats.get("total_games", 0))
    c2.metric("Total Prize Pool", f"₹{stats.get('total_prize_pool', 0):,.0f}")
    c3.metric("Completed", stats.get("completed_games", 0))
    c4.metric("Cancelled", stats.get("cancelled_games", 0))

    st.divider()

    # ── Games Table ────────────────────────────────────────
    games = get_all_games()
    if not games:
        st.warning("No games found.")
        return

    df = pd.DataFrame(games)
    display_df = df[[
        "game_id", "game_type", "game_date", "prize_pool",
        "num_participants", "num_winners", "allocation_method", "status",
    ]].copy()
    display_df.columns = [
        "Game ID", "Type", "Date", "Prize Pool",
        "Players", "Winners", "Allocation", "Status",
    ]
    display_df["Prize Pool"] = display_df["Prize Pool"].apply(lambda x: f"₹{x:,.0f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False)
    st.download_button("📥 Download Games CSV", csv, "games.csv", "text/csv")

    st.divider()

    # ── Game Explorer ──────────────────────────────────────
    st.subheader("🔍 Game Explorer")
    selected_game = st.selectbox(
        "Select Game",
        [g["game_id"] for g in games],
        format_func=lambda x: f"{x} — {next((g['game_type'] + ' — ' + g['description'] for g in games if g['game_id'] == x), '')}",
    )

    if selected_game:
        data = get_game_explorer_data(selected_game)
        if data:
            game = data["game"]

            # Game Info
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"""
            **Game ID:** {game['game_id']}  
            **Type:** {game['game_type']}  
            **Date:** {game['game_date']}
            """)
            col2.markdown(f"""
            **Prize Pool:** ₹{game['prize_pool']:,.0f}  
            **Scenario:** {data['scenario']}  
            **Allocation:** {data['allocation_method']}
            """)
            col3.markdown(f"""
            **Players:** {game['num_participants']}  
            **Winners:** {game['num_winners']}  
            **Status:** {game['status']}
            """)

            # Player Table (Game Explorer)
            st.markdown("#### Player Table")
            if data["player_table"]:
                pt_df = pd.DataFrame(data["player_table"])
                pt_df["buy_in"] = pt_df["buy_in"].apply(lambda x: f"₹{x:,.0f}")
                pt_df["winning"] = pt_df["winning"].apply(lambda x: f"₹{x:,.0f}")
                pt_df["net"] = pt_df["net"].apply(lambda x: f"₹{x:+,.0f}")
                pt_df.columns = ["Player", "PAN", "Buy-in", "Winning", "Net", "Winner?"]
                st.dataframe(pt_df, use_container_width=True, hide_index=True)

            # Validation
            validation = validate_winning_allocation(selected_game)
            if validation.get("valid"):
                st.success(f"✅ {validation.get('message', 'Valid')}")
            elif "error" in validation:
                st.error(f"❌ {validation.get('error')}")

            # Prize pool bar chart
            if data["player_table"]:
                pt_raw = pd.DataFrame(data["player_table"])
                if pt_raw["winning"].sum() > 0:
                    fig = px.bar(
                        pt_raw[pt_raw["winning"] > 0],
                        x="player", y="winning",
                        color="winning",
                        color_continuous_scale="Viridis",
                        labels={"winning": "Winning (₹)", "player": "Player"},
                        title="Winner Allocation",
                    )
                    fig.update_layout(template="plotly_dark", height=300, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
