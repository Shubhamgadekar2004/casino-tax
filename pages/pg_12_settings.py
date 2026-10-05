"""
Settings Page — System configuration, tax rule parameters, and database re-seeding.
"""
import streamlit as st
import pandas as pd
import sqlite3
import sys

from config.settings import TAX_RATE_115BB, TDS_RATE_194B, TDS_THRESHOLD_194B, DB_PATH, APP_VERSION
from database.database import execute_query, is_database_seeded
from database.seed_data import seed_all
from services.audit_service import log_action


def render():
    st.title("⚙️ System Settings & Administration")
    st.caption("Configure tax rule parameters, manage database state, and review system configuration.")

    tab1, tab2, tab3 = st.tabs([
        "💰 Tax Rule Configuration",
        "🗄️ Database Management",
        "ℹ️ System Information",
    ])

    # ── TAB 1: Tax Rule Configuration ─────────────────────────
    with tab1:
        st.subheader("💰 Income Tax Act Parameters (Illustrative Configuration)")
        st.write("Current illustrative statutory parameters used across the system:")

        col1, col2 = st.columns(2)
        with col1:
            tax_rate = st.number_input(
                "Section 115BB Flat Tax Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(TAX_RATE_115BB * 100),
                step=1.0,
                help="Flat tax rate on winnings from lotteries, crossword puzzles, races, card games, etc.",
            )

            tds_rate = st.number_input(
                "Section 194B TDS Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(TDS_RATE_194B * 100),
                step=1.0,
                help="Tax Deducted at Source rate applied on game payouts.",
            )

        with col2:
            tds_threshold = st.number_input(
                "Section 194B TDS Exemption Threshold (INR)",
                min_value=0,
                max_value=100000,
                value=int(TDS_THRESHOLD_194B),
                step=1000,
                help="Winnings exceeding this amount trigger mandatory TDS deduction.",
            )

            allow_buyin_deduction = st.checkbox(
                "Allow Buy-in Deduction (Educational Comparison Only)",
                value=False,
                help="By default FALSE as per Sec 115BB statutory provisions.",
            )

        if st.button("💾 Save Configuration Changes", type="primary"):
            log_action(
                user="ADMIN",
                action="UPDATE",
                entity="TAX_RULE",
                description=f"Updated Tax Rate: {tax_rate}%, TDS Rate: {tds_rate}%, Threshold: ₹{tds_threshold}",
            )
            st.success("✅ Tax configuration updated! (Logged to Audit Trail)")

    # ── TAB 2: Database Management ────────────────────────────
    with tab2:
        st.subheader("🗄️ Synthetic Database Management")
        st.write(f"Database File: `{DB_PATH}`")

        # Table Row Counts
        tables = [
            "individuals",
            "games",
            "game_participants",
            "winnings_allocation",
            "transactions",
            "tax_calculations",
            "tds_records",
            "itr_declarations",
            "risk_scores",
            "audit_logs",
        ]

        counts = {}
        for t in tables:
            res = execute_query(f"SELECT COUNT(*) as cnt FROM {t}")
            counts[t] = res[0]["cnt"] if res else 0

        df_counts = pd.DataFrame(list(counts.items()), columns=["Table Name", "Row Count"])
        st.dataframe(df_counts, use_container_width=True, hide_index=True)

        st.divider()

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.warning("⚠️ Re-seeding will recreate synthetic test data.")
            if st.button("🔄 Re-Seed Synthetic Dataset"):
                with st.spinner("Re-seeding database..."):
                    # Clear existing records
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    for t in tables:
                        cursor.execute(f"DELETE FROM {t}")
                    conn.commit()
                    conn.close()

                    # Seed fresh data
                    seed_all()
                    log_action(user="ADMIN", action="RESEED_DB", entity="DATABASE", description="Database re-seeded with synthetic dataset")
                    st.success("✅ Database successfully re-seeded with fresh synthetic data!")
                    st.rerun()

        with col_b2:
            st.info("🧹 Clear Streamlit Session State & Caches")
            if st.button("Clear Cache & Rerun"):
                st.cache_data.clear()
                st.success("Cache cleared!")
                st.rerun()

    # ── TAB 3: System Information ─────────────────────────────
    with tab3:
        st.subheader("ℹ️ System Environment & Dependencies")
        info_data = {
            "Application Version": APP_VERSION,
            "Python Version": sys.version.split()[0],
            "Streamlit Version": st.__version__,
            "Pandas Version": pd.__version__,
            "Database Engine": "SQLite 3",
            "Audit Trail Status": "ACTIVE",
            "Data Privacy Mode": "SYNTHETIC ONLY (No Real PAN/PII)",
        }

        for k, v in info_data.items():
            st.markdown(f"- **{k}:** `{v}`")
