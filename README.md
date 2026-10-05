# 🎰 Casino Individual Tax & Accounting Demo System

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-FF4B4B.svg)
![Database](https://img.shields.io/badge/database-SQLite-003B57.svg)
![Status](https://img.shields.io/badge/status-Educational%20Prototype-orange.svg)

An end-to-end accounting, tax deduction at source (TDS), and regulatory compliance reconciliation prototype designed for tracking individual casino winnings, calculated liabilities under **Section 115BB**, TDS deduction under **Section 194B**, and automated Income Tax Return (ITR) discrepancy detection.

---

## 🌟 Key Features

- **👤 Individual & Player Ledger Management**: Full profile management with PAN, KYC status tracking, casino account management, and complete transaction histories.
- **🎰 Multi-Player Winnings Allocation Engine**: Dynamic distribution algorithms including Equal Split, Proportional Buy-in, and Winner-Takes-All rules.
- **💰 Tax & TDS Engine**:
  - **Section 115BB**: Flat 30% tax on casino winnings.
  - **Health & Education Cess**: Configurable 4% cess addition.
  - **Section 194B**: 30% Tax Deducted at Source (TDS).
- **📑 Automated ITR Reconciliation**: Compares player-declared ITR income against recorded casino winnings to identify discrepancies (`MATCH`, `UNDER-REPORTED`, `NOT-REPORTED`, `OVER-REPORTED`).
- **⚠️ Automated Risk Scoring Engine**: Evaluates risk vectors (unreported income, large cash flow, high frequency) to assign risk scores (0–100) and risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **🔍 Immutable Audit Logging**: System-wide logging for compliance tracing and regulatory reporting.
- **📊 Professional Export & Reporting**:
  - **PDF Tax Certificates**: Form 16A-style PDF tax certificate generation via ReportLab.
  - **Multi-Tab Excel Exports**: Export entire relational database tables into structured Excel workbooks via OpenPyXL.
- **🧪 Interactive Test Lab**: Run interactive simulations of custom games, participant allocations, and tax calculations.

---

## 📐 Architecture & Project Structure

```text
casino-tax-accounting-demo/
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Python dependencies
├── config/
│   └── settings.py             # Global parameters, tax rates, risk thresholds
├── database/
│   ├── database.py             # SQLite connection & query helpers
│   ├── schema.sql              # Relational database schema
│   └── seed_data.py            # Synthetic demo data generator (Faker)
├── models/                     # Data access objects (DAOs)
│   ├── individual.py
│   ├── game.py
│   └── transaction.py
├── services/                   # Business logic services
│   ├── tax_service.py          # Tax & TDS calculations
│   ├── winnings_service.py     # Prize pool allocation engine
│   ├── reconciliation_service.py # ITR vs Casino winnings matcher
│   ├── risk_service.py         # Automated risk scoring engine
│   ├── audit_service.py        # Audit trail logger
│   └── report_service.py       # PDF certificate & Excel generators
├── pages/                      # Streamlit UI modules (12 view components)
│   ├── pg_01_dashboard.py
│   ├── pg_02_individuals.py
│   ├── pg_03_games.py
│   ├── pg_04_transactions.py
│   ├── pg_05_player_ledger.py
│   ├── pg_06_tax_calculator.py
│   ├── pg_07_itr_reconciliation.py
│   ├── pg_08_risk_dashboard.py
│   ├── pg_09_audit_trail.py
│   ├── pg_10_reports.py
│   ├── pg_11_test_lab.py
│   └── pg_12_settings.py
└── tests/
    └── test_tax_and_services.py # Comprehensive Pytest suite
```

---

## 🧮 Tax Calculation Mechanics

| Component | Tax Section | Rate / Formula | Notes |
| :--- | :--- | :--- | :--- |
| **Taxable Winnings** | Sec 115BB | Gross Winnings | Deductions for buy-in/expenses not permissible u/s 115BB |
| **Base Tax Amount** | Sec 115BB | 30% of Gross Winnings | Flat rate tax |
| **Health & Education Cess** | General | 4% of Base Tax Amount | Added to base tax liability |
| **Total Calculated Tax** | - | `Base Tax + Cess` | Effective rate = 31.2% |
| **TDS Deducted** | Sec 194B | 30% of Gross Winnings | Deducted at payout by casino deductor |
| **Net Payout** | - | `Gross Winnings - TDS` | Payout received by player |

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python**: Version `3.10` or higher
- **pip** package manager

### 1. Clone & Set Up Environment

```bash
# Navigate to project directory
cd casino-tax-accounting-demo

# Create virtual environment
python3 -m venv venv

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Activate virtual environment (Windows)
# venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch the Application

```bash
streamlit run app.py
```

The app will automatically initialize SQLite database schema and seed synthetic demonstration data on first start. Access the application in your browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the test suite to verify tax calculations, winnings allocation algorithms, database queries, and report generation:

```bash
pytest
```

Or run via `unittest`:

```bash
python -m unittest tests/test_tax_and_services.py
```

---

## 📊 Modules & Navigation Overview

1. **🏠 Dashboard**: System KPIs, total gross winnings, TDS collected, risk distribution charts, and quick actions.
2. **👤 Individuals**: View and search player profiles, PAN details, KYC status, and risk tiers.
3. **🎰 Games**: Manage games, prize pools, participant entries, and winning payouts.
4. **💳 Transactions**: Immutable transaction ledger (Buy-ins, Winnings, Redemptions, TDS entries).
5. **📒 Player Ledger**: Detailed statement of account for individual players.
6. **💰 Tax Calculator**: Interactive calculator for gross winnings, cess, TDS, and net payouts.
7. **📑 ITR Reconciliation**: Reconcile casino records with tax returns, flag under-reported income.
8. **⚠️ Risk Dashboard**: Heatmaps, high-risk flag monitoring, and automated compliance risk scores.
9. **🔍 Audit Trail**: Searchable audit logs of system actions and data edits.
10. **📊 Reports**: On-demand generation and download of PDF Tax Certificates and Excel multi-tab workbooks.
11. **🧪 Test Lab**: Sandbox for testing winning distribution algorithms and tax scenarios.
12. **⚙️ Settings**: Configurable tax parameters, cess rates, and risk scoring rule weights.

---

## ⚠️ Disclaimer

This system is an **educational and research demonstration prototype**. All data generated and used within this system is synthetic. Prior to any real-world deployment or official accounting usage, verify current tax regulations with qualified tax professionals and statutory authorities.
