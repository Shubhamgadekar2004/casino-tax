"""
Casino Individual Tax & Accounting Demo System
Main Application Entry Point

Run: streamlit run app.py
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import APP_TITLE, APP_ICON, APP_VERSION
from database.database import init_database, is_database_seeded
from database.seed_data import seed_all


def setup_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
    <style>
        /* Main theme */
        .stApp {
            background-color: #0e1117;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
            border: 1px solid #2d3548;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            color: #8b95a5 !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%);
            border-right: 1px solid #2d3548;
        }

        /* Headers */
        h1, h2, h3 {
            color: #e6eaf0 !important;
        }

        /* Dataframes */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid #3d4654;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            border-color: #667eea;
            box-shadow: 0 0 12px rgba(102, 126, 234, 0.3);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 8px 20px;
        }

        /* Expander */
        [data-testid="stExpander"] {
            background: #1a1f2e;
            border: 1px solid #2d3548;
            border-radius: 8px;
        }

        /* Selectbox */
        [data-testid="stSelectbox"] {
            border-radius: 8px;
        }

        /* Info/Warning boxes */
        .stAlert {
            border-radius: 8px;
        }

        /* Custom status badges */
        .status-match { color: #00d97e; font-weight: bold; }
        .status-under { color: #e63757; font-weight: bold; }
        .status-over { color: #f6c23e; font-weight: bold; }
        .status-not { color: #e63757; font-weight: bold; }
        .status-review { color: #f6c23e; font-weight: bold; }

        .risk-low { color: #00d97e; }
        .risk-medium { color: #f6c23e; }
        .risk-high { color: #fd7e14; }
        .risk-critical { color: #e63757; }

        /* Disclaimer */
        .disclaimer {
            background: #2a1f1f;
            border-left: 4px solid #e63757;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin: 8px 0;
            font-size: 0.85rem;
            color: #e6a0a0;
        }
    </style>
    """, unsafe_allow_html=True)


def init_app():
    """Initialize database and seed data if needed."""
    if "db_initialized" not in st.session_state:
        init_database()
        if not is_database_seeded():
            with st.spinner("🎰 Initializing demo data..."):
                seed_all()
        st.session_state.db_initialized = True


def render_sidebar():
    """Render the navigation sidebar."""
    with st.sidebar:
        st.markdown(f"# {APP_ICON} Casino Tax Demo")
        st.caption(f"v{APP_VERSION} — Educational / Research Prototype")
        st.divider()

        page = st.radio(
            "Navigation",
            [
                "🏠 Dashboard",
                "👤 Individuals",
                "🎰 Games",
                "💳 Transactions",
                "📒 Player Ledger",
                "💰 Tax Calculator",
                "📑 ITR Reconciliation",
                "⚠️ Risk Dashboard",
                "🔍 Audit Trail",
                "📊 Reports",
                "🧪 Test Lab",
                "⚙️ Settings",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown(
            '<div class="disclaimer">'
            "⚠️ Illustrative configuration — verify current Indian tax law "
            "before real-world use."
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("All data is synthetic. No real PAN or personal data.")

    return page


def main():
    setup_page()
    init_app()
    page = render_sidebar()

    # Route to pages
    if page == "🏠 Dashboard":
        from pages.pg_01_dashboard import render
        render()
    elif page == "👤 Individuals":
        from pages.pg_02_individuals import render
        render()
    elif page == "🎰 Games":
        from pages.pg_03_games import render
        render()
    elif page == "💳 Transactions":
        from pages.pg_04_transactions import render
        render()
    elif page == "📒 Player Ledger":
        from pages.pg_05_player_ledger import render
        render()
    elif page == "💰 Tax Calculator":
        from pages.pg_06_tax_calculator import render
        render()
    elif page == "📑 ITR Reconciliation":
        from pages.pg_07_itr_reconciliation import render
        render()
    elif page == "⚠️ Risk Dashboard":
        from pages.pg_08_risk_dashboard import render
        render()
    elif page == "🔍 Audit Trail":
        from pages.pg_09_audit_trail import render
        render()
    elif page == "📊 Reports":
        from pages.pg_10_reports import render
        render()
    elif page == "🧪 Test Lab":
        from pages.pg_11_test_lab import render
        render()
    elif page == "⚙️ Settings":
        from pages.pg_12_settings import render
        render()


if __name__ == "__main__":
    main()
