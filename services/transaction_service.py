"""
Transaction Service — business logic for the transaction ledger.
"""
from models.transaction import (
    get_all_transactions, get_transactions_by_pan,
    get_transaction_summary, get_individual_ledger,
)
from database.database import execute_query


def get_dashboard_kpis():
    """Get key performance indicators for the dashboard."""
    kpis = execute_query(
        """
        SELECT
            COUNT(*) as total_transactions,
            SUM(CASE WHEN credit_debit = 'CREDIT' THEN amount ELSE 0 END) as total_credits,
            SUM(CASE WHEN credit_debit = 'DEBIT' THEN amount ELSE 0 END) as total_debits,
            SUM(CASE WHEN transaction_type = 'WINNING' THEN amount ELSE 0 END) as total_winnings,
            SUM(CASE WHEN transaction_type = 'BUY_IN' THEN amount ELSE 0 END) as total_buyins,
            SUM(CASE WHEN transaction_type = 'TDS' THEN amount ELSE 0 END) as total_tds,
            SUM(CASE WHEN transaction_type = 'REDEMPTION' THEN amount ELSE 0 END) as total_redemptions,
            COUNT(DISTINCT pan) as unique_players
        FROM transactions
        """
    )
    return kpis[0] if kpis else {}


def get_monthly_transaction_summary():
    """Get monthly aggregate of transactions."""
    return execute_query(
        """
        SELECT
            strftime('%Y-%m', transaction_date) as month,
            transaction_type,
            COUNT(*) as count,
            SUM(amount) as total
        FROM transactions
        GROUP BY month, transaction_type
        ORDER BY month, transaction_type
        """
    )


def get_payment_method_distribution():
    """Get distribution by payment method."""
    return execute_query(
        """
        SELECT payment_method,
               COUNT(*) as count,
               SUM(amount) as total
        FROM transactions
        WHERE payment_method IS NOT NULL AND payment_method != 'SYSTEM'
        GROUP BY payment_method
        ORDER BY total DESC
        """
    )
