"""
Tax Calculator Page — Configurable illustrative tax engine.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from services.tax_service import (
    calculate_tax, calculate_tds, get_tax_summary_for_individual,
    get_aggregate_tax_stats,
)
from models.tax import get_all_tds_records, get_tax_calculations, get_active_tax_config
from models.individual import get_all_individuals
from config.settings import TAX_CONFIG


def render():
    st.title("💰 Tax Calculator")
    st.caption("Illustrative Tax Engine — Configurable Rates")

    st.markdown(
        '<div class="disclaimer">'
        "⚠️ Illustrative configuration — verify current Indian tax law "
        "before real-world use."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Tax Configuration ──────────────────────────────────
    with st.expander("⚙️ Current Tax Configuration", expanded=True):
        config = get_active_tax_config()
        if config:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tax Rate", f"{config['tax_rate']*100:.0f}%")
            c2.metric("Cess Rate", f"{config['cess_rate']*100:.0f}%")
            c3.metric("TDS Rate", f"{config['tds_rate']*100:.0f}%")
            c4.metric("Effective Date", config["effective_date"])
            st.caption(f"Category: {config['income_category']}")

    st.divider()

    # ── Interactive Calculator ─────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🧮 Calculator", "📋 All Tax Calculations", "💳 TDS Records"])

    with tab1:
        st.subheader("Interactive Tax Calculator")

        col1, col2 = st.columns(2)

        with col1:
            calc_mode = st.radio("Mode", ["Enter Amount", "Select Individual"])

            if calc_mode == "Enter Amount":
                gross = st.number_input(
                    "Gross Winnings (₹)", min_value=0, value=100000, step=10000,
                )
                result = calculate_tax(gross)
            else:
                individuals = get_all_individuals()
                selected_pan = st.selectbox(
                    "Select Individual",
                    [i["pan"] for i in individuals],
                    format_func=lambda x: f"{x} — {next((i['first_name'] + ' ' + i['last_name'] for i in individuals if i['pan'] == x), '')}",
                )
                result = get_tax_summary_for_individual(selected_pan)

        with col2:
            if result:
                st.markdown("### Tax Breakdown")
                st.markdown(f"""
                | Component | Amount |
                |---|---|
                | **Gross Winnings** | ₹{result['gross_winnings']:,.2f} |
                | **Taxable Winnings** | ₹{result['taxable_winnings']:,.2f} |
                | Tax @ {result['tax_rate']*100:.0f}% | ₹{result['tax_amount']:,.2f} |
                | Cess @ {result['cess_rate']*100:.0f}% | ₹{result['cess_amount']:,.2f} |
                | Surcharge | ₹{result['surcharge_amount']:,.2f} |
                | **Total Tax** | **₹{result['total_tax']:,.2f}** |
                | TDS Deducted | ₹{result['tds_amount']:,.2f} |
                | **Balance Payable** | **₹{result['balance_payable']:,.2f}** |
                | Effective Rate | {result['effective_rate']:.2f}% |
                """)

                # Donut chart
                fig = go.Figure(data=[go.Pie(
                    labels=["Tax", "Cess", "Surcharge", "Net Payout"],
                    values=[
                        result["tax_amount"],
                        result["cess_amount"],
                        result["surcharge_amount"],
                        result["gross_winnings"] - result["total_tax"],
                    ],
                    hole=0.5,
                    marker_colors=["#e63757", "#f6c23e", "#fd7e14", "#00d97e"],
                )])
                fig.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("All Tax Calculations")
        calcs = get_tax_calculations()
        if calcs:
            df = pd.DataFrame(calcs)
            display_cols = [
                "pan", "first_name", "last_name", "assessment_year",
                "gross_winnings", "total_tax", "tds_deducted", "balance_payable",
            ]
            df_display = df[display_cols].copy()
            for col in ["gross_winnings", "total_tax", "tds_deducted", "balance_payable"]:
                df_display[col] = df_display[col].apply(lambda x: f"₹{x:,.2f}")
            df_display.columns = [
                "PAN", "First Name", "Last Name", "AY",
                "Gross Winnings", "Total Tax", "TDS", "Balance",
            ]
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            csv = pd.DataFrame(calcs).to_csv(index=False)
            st.download_button("📥 Download Tax Calculations CSV", csv, "tax_calculations.csv", "text/csv")

    with tab3:
        st.subheader("TDS Records")
        tds_records = get_all_tds_records()
        if tds_records:
            df_tds = pd.DataFrame(tds_records)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total TDS Records", len(df_tds))
            c2.metric("Total Gross", f"₹{df_tds['gross_amount'].sum():,.0f}")
            c3.metric("Total TDS Deducted", f"₹{df_tds['tds_amount'].sum():,.0f}")

            display_tds = df_tds[[
                "tds_id", "pan", "first_name", "last_name",
                "game_id", "gross_amount", "tds_rate", "tds_amount", "status",
            ]].copy()
            for col in ["gross_amount", "tds_amount"]:
                display_tds[col] = display_tds[col].apply(lambda x: f"₹{x:,.2f}")
            display_tds["tds_rate"] = display_tds["tds_rate"].apply(lambda x: f"{float(x)*100:.0f}%")
            display_tds.columns = [
                "TDS ID", "PAN", "First Name", "Last Name",
                "Game", "Gross Amount", "TDS Rate", "TDS Amount", "Status",
            ]
            st.dataframe(display_tds, use_container_width=True, hide_index=True)

            csv = df_tds.to_csv(index=False)
            st.download_button("📥 Download TDS CSV", csv, "tds_records.csv", "text/csv")
