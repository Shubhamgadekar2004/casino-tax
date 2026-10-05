"""
Reports Page — PDF Tax Certificate generation and Excel data exports.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from models.individual import get_all_individuals
from services.report_service import generate_pdf_tax_certificate, generate_excel_export
from database.database import execute_query


def render():
    st.title("📊 Compliance & Tax Reports")
    st.caption("Generate official PDF Tax Certificates, export multi-tab Excel database audits, and build custom report queries.")

    tab1, tab2, tab3 = st.tabs([
        "📄 Individual PDF Tax Certificate",
        "📁 Full Database Excel Export",
        "📈 Custom Data Query & Export",
    ])

    # ── TAB 1: PDF Tax Certificate Generator ──────────────────
    with tab1:
        st.subheader("📄 Generate Tax & TDS Certificate (Form 16A Equivalent)")
        st.write("Select an individual taxpayer to generate a formatted PDF tax statement containing buy-ins, winnings, TDS deductions, and tax compliance summary.")

        individuals = get_all_individuals()
        ind_options = {f"{ind['name']} ({ind['pan']}) - ID: {ind['individual_id']}": ind['individual_id'] for ind in individuals}

        selected_label = st.selectbox("Select Taxpayer:", list(ind_options.keys()))

        if selected_label:
            ind_id = ind_options[selected_label]
            ind_data = [i for i in individuals if i['individual_id'] == ind_id][0]

            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"""
                **Taxpayer Details:**
                - **Name:** {ind_data['name']}
                - **PAN:** {ind_data['pan']}
                - **KYC ID:** {ind_data['kyc_id']}
                - **Risk Tier:** {ind_data['risk_tier'].upper()}
                """)

            with col_b:
                st.write("**Report Generation Settings:**")
                st.checkbox("Include detailed game-by-game breakdown", value=True)
                st.checkbox("Include Section 115BB / 194B tax explanation", value=True)

                if st.button("🔨 Generate PDF Certificate", type="primary"):
                    try:
                        pdf_bytes = generate_pdf_tax_certificate(ind_id)
                        st.success("✅ PDF Tax Certificate generated successfully!")
                        st.download_button(
                            label=f"📥 Download PDF ({ind_data['pan']}_Tax_Certificate.pdf)",
                            data=pdf_bytes,
                            file_name=f"{ind_data['pan']}_Tax_Certificate.pdf",
                            mime="application/pdf",
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")

    # ── TAB 2: Full Excel Export ──────────────────────────────
    with tab2:
        st.subheader("📁 Complete Database Excel Audit Workbook")
        st.write("Download the entire Casino Tax Demonstration system database as an Excel workbook with 10 formatted tabs:")

        st.markdown("""
        - 👤 **Individuals** (KYC, PAN, Risk Tier)
        - 🎰 **Games** (Sessions, Prize Pools, Status)
        - 👥 **Participants** (Players in each game session)
        - 🏆 **Winnings Allocation** (Rule engine allocations)
        - 💳 **Transactions** (Ledger entries)
        - 💰 **Tax Calculations** (30% u/s 115BB calculations)
        - 📄 **TDS Records** (30% u/s 194B deductions)
        - 📑 **ITR Declarations** (Declared income vs casino logs)
        - ⚠️ **Risk Scores** (Automated risk factor breakdown)
        - 🔍 **Audit Logs** (Immutable log history)
        """)

        st.divider()

        if st.button("📊 Build Excel Audit Package", type="primary"):
            with st.spinner("Compiling multi-tab Excel file..."):
                excel_bytes = generate_excel_export()
                st.success("✅ Excel export ready!")
                st.download_button(
                    label=f"📥 Download Full Database Excel ({datetime.now().strftime('%Y%m%d')}_Casino_Tax_Export.xlsx)",
                    data=excel_bytes,
                    file_name=f"Casino_Tax_Export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    # ── TAB 3: Custom Data Query ──────────────────────────────
    with tab3:
        st.subheader("📈 Custom Table Exporter")
        st.write("Select a table, preview the data, and export directly as CSV or JSON.")

        table_name = st.selectbox(
            "Select Database Table:",
            [
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
            ],
        )

        query = f"SELECT * FROM {table_name}"
        df_table = pd.DataFrame(execute_query(query))

        st.write(f"Previewing **{table_name}** ({len(df_table)} rows):")
        st.dataframe(df_table, use_container_width=True, hide_index=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            csv_data = df_table.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Export {table_name}.csv",
                data=csv_data,
                file_name=f"{table_name}.csv",
                mime="text/csv",
            )
        with col_c2:
            json_data = df_table.to_json(orient="records", indent=2)
            st.download_button(
                label=f"📥 Export {table_name}.json",
                data=json_data,
                file_name=f"{table_name}.json",
                mime="application/json",
            )
