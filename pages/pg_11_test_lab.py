"""
Test Lab Page — Interactive scenario simulation and automated testing environment.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
import sys

from services.tax_service import calculate_game_tax
from services.winnings_service import allocate_winnings
from services.risk_service import calculate_risk_score


def render():
    st.title("🧪 Interactive Test Lab & Simulator")
    st.caption("Simulate custom allocation rules, tax rate variations, risk score triggers, and execute unit test suites.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎲 Allocation Rule Simulator",
        "💰 Tax Calculator Playground",
        "⚠️ Risk Engine Simulator",
        "⚙️ System Unit Tests",
    ])

    # ── TAB 1: Allocation Rule Simulator ──────────────────────
    with tab1:
        st.subheader("🎲 Game Winnings Allocation Simulator")
        st.write("Simulate how a multi-player game prize pool is allocated among participants under different rules.")

        col1, col2 = st.columns(2)
        with col1:
            prize_pool = st.number_input("Total Prize Pool (INR)", min_value=1000, max_value=10000000, value=100000, step=10000)
            rule = st.selectbox("Allocation Rule:", ["EQUAL_SPLIT", "PROPORTIONAL_BUYIN", "WINNER_TAKES_ALL", "RANKED_TIER"])
            house_commission_pct = st.slider("House Rake / Commission (%)", 0.0, 15.0, 5.0, 0.5)

        with col2:
            st.write("**Player Buy-ins:**")
            p1_buyin = st.number_input("Player 1 Buy-in", value=20000)
            p2_buyin = st.number_input("Player 2 Buy-in", value=30000)
            p3_buyin = st.number_input("Player 3 Buy-in", value=50000)

        participants = [
            {"participant_id": "P1", "individual_id": "IND-001", "name": "Player 1", "buy_in": p1_buyin, "rank": 1},
            {"participant_id": "P2", "individual_id": "IND-002", "name": "Player 2", "buy_in": p2_buyin, "rank": 2},
            {"participant_id": "P3", "individual_id": "IND-003", "name": "Player 3", "buy_in": p3_buyin, "rank": 3},
        ]

        net_prize_pool = prize_pool * (1 - house_commission_pct / 100.0)
        st.info(f"Gross Pool: ₹{prize_pool:,.2f} | House Rake ({house_commission_pct}%): ₹{(prize_pool - net_prize_pool):,.2f} | Net Pool Distributed: ₹{net_prize_pool:,.2f}")

        if st.button("▶ Run Allocation Simulation", type="primary"):
            allocations = allocate_winnings("GAME-SIM", net_prize_pool, participants, rule=rule)

            df_sim = pd.DataFrame(allocations)
            df_sim["buy_in"] = [p["buy_in"] for p in participants]
            df_sim["net_profit"] = df_sim["allocated_amount"] - df_sim["buy_in"]
            df_sim["tds_estimate"] = df_sim["allocated_amount"] * 0.30

            st.dataframe(
                df_sim[["participant_id", "buy_in", "allocated_amount", "net_profit", "tds_estimate"]],
                use_container_width=True,
                hide_index=True,
            )

            fig = px.bar(
                df_sim,
                x="participant_id",
                y=["buy_in", "allocated_amount", "tds_estimate"],
                barmode="group",
                title="Simulation: Buy-in vs Winnings Allocated vs TDS",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── TAB 2: Tax Calculator Playground ──────────────────────
    with tab2:
        st.subheader("💰 What-If Tax Rate Simulator")
        st.write("Evaluate net income impact across different tax rate structures and surcharge brackets.")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            sim_gross_winnings = st.number_input("Gross Winnings (INR)", value=500000, step=50000)
            sim_buy_in = st.number_input("Total Buy-in Invested (INR)", value=100000, step=10000)
            sim_rate = st.slider("Base Tax Rate u/s 115BB (%)", 10.0, 50.0, 30.0, 1.0)
            surcharge_pct = st.slider("Health & Education Cess / Surcharge (%)", 0.0, 15.0, 4.0, 0.5)

        effective_rate = sim_rate * (1 + surcharge_pct / 100.0)
        tax_amount = sim_gross_winnings * (effective_rate / 100.0)
        net_after_tax = sim_gross_winnings - tax_amount

        with col_t2:
            st.metric("Effective Tax Rate", f"{effective_rate:.2f}%")
            st.metric("Total Tax & Cess Payable", f"₹{tax_amount:,.2f}")
            st.metric("Net Retention After Tax", f"₹{net_after_tax:,.2f}")

            # Note on Sec 115BB non-deductibility
            st.warning("""
            ⚠️ **Section 115BB Tax Note:**
            Under Section 115BB of the Indian Income Tax Act, no deduction in respect of any expenditure or allowance is allowed against winnings from lotteries, crossword puzzles, races, or card games.
            Therefore, buy-in of ₹{:,.0f} cannot be deducted from gross winnings for tax computation.
            """.format(sim_buy_in))

    # ── TAB 3: Risk Engine Simulator ──────────────────────────
    with tab3:
        st.subheader("⚠️ Risk Scoring Scenario Simulator")
        st.write("Test how changing individual parameters affects automated risk scoring and flagging.")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            sim_winnings = st.number_input("Total Casino Winnings", value=2000000, step=100000)
            sim_buyin = st.number_input("Total Casino Buy-in", value=500000, step=50000)
            sim_itr = st.number_input("Declared ITR Casino Winnings", value=500000, step=100000)
            sim_win_count = st.slider("Total Game Wins Count", 1, 50, 15)

        # Build synthetic individual for risk calc
        mock_ind = {
            "individual_id": "IND-SIM",
            "name": "Simulated Player",
            "pan": "ABCDE1234F",
            "kyc_status": "VERIFIED",
        }

        # Dynamic risk logic simulation
        win_buy_ratio = sim_winnings / max(1, sim_buyin)
        itr_diff = abs(sim_winnings - sim_itr)
        unreported_pct = (itr_diff / max(1, sim_winnings)) * 100

        mock_risk = calculate_risk_score("IND-SIM")

        with col_r2:
            st.markdown(f"**Win-to-Buyin Ratio:** `{win_buy_ratio:.2f}x`")
            st.markdown(f"**Unreported Winnings Gap:** `₹{itr_diff:,.0f}` (`{unreported_pct:.1f}%`)")

            st.metric("Calculated Risk Score", f"{mock_risk['risk_score']} / 100")
            st.metric("Assigned Risk Tier", mock_risk['risk_tier'].upper())

            st.write("**Risk Factors Breakdown:**")
            st.json(mock_risk["risk_factors"])

    # ── TAB 4: Unit Test Suite Runner ─────────────────────────
    with tab4:
        st.subheader("⚙️ Run Automated Unit & System Test Suite")
        st.write("Execute pytest suite to verify calculation accuracy, allocation rules, database schemas, and reconciliation integrity.")

        if st.button("🧪 Execute Pytest Suite", type="primary"):
            with st.spinner("Running unit tests..."):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        st.success("✅ All unit tests PASSED successfully!")
                    else:
                        st.error("❌ Some unit tests failed or produced warnings.")

                    st.code(result.stdout if result.stdout else result.stderr)

                except Exception as e:
                    st.error(f"Error executing test suite: {str(e)}")
