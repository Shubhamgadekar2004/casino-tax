"""
Tax Model — data access for tax configurations, calculations, and TDS records.
"""
from database.database import execute_query


def get_active_tax_config():
    rows = execute_query(
        "SELECT * FROM tax_configurations WHERE is_active = 1 ORDER BY effective_date DESC LIMIT 1"
    )
    return rows[0] if rows else None


def get_all_tax_configs():
    return execute_query("SELECT * FROM tax_configurations ORDER BY effective_date DESC")


def get_tax_calculations():
    return execute_query(
        """
        SELECT tc.*, i.first_name, i.last_name
        FROM tax_calculations tc
        JOIN individuals i ON tc.individual_id = i.individual_id
        ORDER BY tc.gross_winnings DESC
        """
    )


def get_tax_calculation_by_pan(pan: str):
    rows = execute_query(
        "SELECT * FROM tax_calculations WHERE pan = ?", (pan,)
    )
    return rows[0] if rows else None


def get_all_tds_records():
    return execute_query(
        """
        SELECT t.*, i.first_name, i.last_name
        FROM tds_records t
        JOIN individuals i ON t.pan = i.pan
        ORDER BY t.deduction_date DESC
        """
    )


def get_tds_by_pan(pan: str):
    return execute_query(
        "SELECT * FROM tds_records WHERE pan = ? ORDER BY deduction_date DESC",
        (pan,),
    )


def get_tds_summary():
    return execute_query(
        """
        SELECT pan,
               COUNT(*) as num_records,
               SUM(gross_amount) as total_gross,
               SUM(tds_amount) as total_tds
        FROM tds_records
        GROUP BY pan
        ORDER BY total_tds DESC
        """
    )
