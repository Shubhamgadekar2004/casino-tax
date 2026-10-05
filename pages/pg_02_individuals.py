"""
Individuals Page — KYC, PAN, registration, and account details.
"""
import streamlit as st
import pandas as pd

from models.individual import get_all_individuals, get_individual_summary, search_individuals


def render():
    st.title("👤 Individuals")
    st.caption("20 Synthetic Individuals — KYC, PAN, Casino Accounts")

    # ── Search ─────────────────────────────────────────────
    search = st.text_input("🔍 Search by PAN, Name", placeholder="e.g. TEST0001X or John")

    if search:
        individuals = search_individuals(search)
    else:
        individuals = get_all_individuals()

    if not individuals:
        st.warning("No individuals found.")
        return

    # ── Summary KPIs ───────────────────────────────────────
    df = pd.DataFrame(individuals)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Individuals", len(df))
    c2.metric("KYC Verified", len(df[df["kyc_status"] == "VERIFIED"]))
    c3.metric("KYC Pending", len(df[df["kyc_status"] == "PENDING"]))
    c4.metric("Active", len(df[df["status"] == "ACTIVE"]))

    st.divider()

    # ── Data Table ─────────────────────────────────────────
    display_df = df[[
        "individual_id", "pan", "first_name", "last_name",
        "mobile", "kyc_status", "registration_date", "risk_score",
    ]].copy()
    display_df.columns = [
        "ID", "PAN", "First Name", "Last Name",
        "Mobile", "KYC Status", "Registered", "Risk Score",
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk Score": st.column_config.ProgressColumn(
                min_value=0, max_value=100, format="%d",
            ),
        },
    )

    # ── CSV Download ───────────────────────────────────────
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        csv,
        "individuals.csv",
        "text/csv",
    )

    st.divider()

    # ── Individual Detail ──────────────────────────────────
    st.subheader("📋 Individual Detail")
    selected_id = st.selectbox(
        "Select Individual",
        [i["individual_id"] for i in individuals],
        format_func=lambda x: f"{x} — {next((i['first_name'] + ' ' + i['last_name'] for i in individuals if i['individual_id'] == x), '')}",
    )

    if selected_id:
        summary = get_individual_summary(selected_id)
        if summary:
            ind = summary["individual"]
            totals = summary["totals"]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Personal Details")
                st.markdown(f"""
                | Field | Value |
                |---|---|
                | **Individual ID** | {ind['individual_id']} |
                | **PAN** | {ind['pan']} |
                | **Name** | {ind['first_name']} {ind['last_name']} |
                | **Email** | {ind['email']} |
                | **Mobile** | {ind['mobile']} |
                | **DOB** | {ind['date_of_birth']} |
                | **KYC Status** | {ind['kyc_status']} |
                | **Registration** | {ind['registration_date']} |
                """)

            with col2:
                st.markdown("#### Account Summary")
                st.metric("Total Buy-ins", f"₹{totals['total_buyins']:,.2f}")
                st.metric("Total Winnings", f"₹{totals['total_winnings']:,.2f}")
                st.metric("Total TDS", f"₹{totals['total_tds']:,.2f}")
                st.metric("Net Result", f"₹{totals['net_result']:,.2f}")
                st.metric("Games Played", totals["games_played"])
                st.metric("Games Won", totals["games_won"])

            # Casino Accounts
            if summary["accounts"]:
                with st.expander("🏦 Casino Accounts"):
                    st.dataframe(
                        pd.DataFrame(summary["accounts"]),
                        use_container_width=True,
                        hide_index=True,
                    )
