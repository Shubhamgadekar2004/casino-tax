"""
Application Settings and Configuration
Casino Individual Tax & Accounting Demo System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "casino_demo.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
DB_PATH = DATABASE_PATH

# Tax Aliases
TAX_RATE_115BB = 0.30
TDS_RATE_194B = 0.30
TDS_THRESHOLD_194B = 10000.0

# Application
APP_TITLE = "Casino Individual Tax & Accounting Demo"
APP_ICON = "🎰"
APP_VERSION = "1.0.0"

# Demo identifiers
DEMO_USERS = ["ADMIN", "SYSTEM", "DEMO_USER"]

# Tax Configuration (Illustrative — verify current Indian tax law before real-world use)
TAX_CONFIG = {
    "tax_rate": 0.30,            # 30% illustrative special rate
    "cess_rate": 0.04,           # 4% Health & Education Cess
    "surcharge_rate": 0.00,      # Surcharge (configurable)
    "tds_rate": 0.30,            # 30% TDS on winnings
    "effective_date": "2024-04-01",
    "income_category": "Income from Other Sources — Casino Winnings",
    "disclaimer": (
        "Illustrative configuration — verify current Indian tax law "
        "before real-world use."
    ),
}

# Risk Scoring Rules
RISK_RULES = {
    "winnings_not_reported": 40,
    "large_under_reporting": 30,
    "repeated_mismatches": 20,
    "large_cash_activity": 10,
    "frequent_high_value_txns": 10,
}

RISK_THRESHOLDS = {
    "LOW": (0, 30),
    "MEDIUM": (31, 60),
    "HIGH": (61, 80),
    "CRITICAL": (81, 100),
}

# Currency formatting
CURRENCY_SYMBOL = "₹"
CURRENCY_LOCALE = "en_IN"

# Game types
GAME_TYPES = ["Roulette", "Blackjack", "Poker", "Baccarat", "Slot Tournament"]

# Winner allocation methods
ALLOCATION_METHODS = [
    "SINGLE_WINNER",
    "EQUAL_SHARE",
    "PERCENTAGE_BASED",
    "FIXED_AMOUNT",
    "NO_WINNER",
]

# Transaction types
TRANSACTION_TYPES = [
    "BUY_IN",
    "GAME_ENTRY",
    "WINNING",
    "REDEMPTION",
    "REFUND",
    "ADJUSTMENT",
    "TDS",
]

# Reconciliation statuses
RECONCILIATION_STATUSES = [
    "MATCH",
    "REVIEW",
    "UNDER-REPORTED",
    "NOT-REPORTED",
    "OVER-REPORTED",
]

# Casino names for demo
CASINO_NAMES = [
    "Demo Royal Casino",
    "Demo Grand Palace",
    "Demo Golden Ace",
    "Demo Star Club",
    "Demo Diamond Arena",
]

# Report settings
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Data directory
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Page configuration
PAGES = {
    "Dashboard": {"icon": "🏠", "file": "01_dashboard"},
    "Individuals": {"icon": "👤", "file": "02_individuals"},
    "Games": {"icon": "🎰", "file": "03_games"},
    "Transactions": {"icon": "💳", "file": "04_transactions"},
    "Player Ledger": {"icon": "📒", "file": "05_player_ledger"},
    "Tax Calculator": {"icon": "💰", "file": "06_tax_calculator"},
    "ITR Reconciliation": {"icon": "📑", "file": "07_itr_reconciliation"},
    "Risk Dashboard": {"icon": "⚠️", "file": "08_risk_dashboard"},
    "Audit Trail": {"icon": "🔍", "file": "09_audit_trail"},
    "Reports": {"icon": "📊", "file": "10_reports"},
    "Test Lab": {"icon": "🧪", "file": "11_test_lab"},
    "Settings": {"icon": "⚙️", "file": "12_settings"},
}
