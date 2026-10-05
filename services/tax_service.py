"""
Tax Service — configurable tax engine.
Illustrative configuration — verify current Indian tax law before real-world use.
"""
from config.settings import TAX_CONFIG
from database.database import execute_query


def calculate_tax(individual_id_or_gross, config: dict = None) -> dict:
    """
    Calculate illustrative tax on casino winnings.
    Accepts either gross_winnings (float/int) or individual_id (str).
    """
    cfg = config or TAX_CONFIG

    if isinstance(individual_id_or_gross, str):
        # Fetch total gross winnings & buy-ins for individual_id
        ind_winnings = execute_query(
            """
            SELECT COALESCE(SUM(gross_winning), 0) as total_gross
            FROM winning_allocations
            WHERE individual_id = ?
            """,
            (individual_id_or_gross,),
        )
        gross_winnings = ind_winnings[0]["total_gross"] if ind_winnings else 0.0

        ind_buyins = execute_query(
            """
            SELECT COALESCE(SUM(buy_in_amount), 0) as total_buyin
            FROM game_participants
            WHERE individual_id = ?
            """,
            (individual_id_or_gross,),
        )
        total_buy_in = ind_buyins[0]["total_buyin"] if ind_buyins else 0.0
    else:
        gross_winnings = float(individual_id_or_gross or 0)
        total_buy_in = 0.0

    taxable_winnings = gross_winnings
    tax_amount = round(taxable_winnings * cfg["tax_rate"], 2)
    cess_amount = round(tax_amount * cfg["cess_rate"], 2)
    surcharge_amount = round(tax_amount * cfg["surcharge_rate"], 2)
    total_tax = round(tax_amount + cess_amount + surcharge_amount, 2)
    tds_amount = round(gross_winnings * cfg["tds_rate"], 2)
    balance_payable = round(total_tax - tds_amount, 2)
    net_payout = round(gross_winnings - tds_amount, 2)

    return {
        "gross_winnings": gross_winnings,
        "total_buy_in": total_buy_in,
        "net_winnings": gross_winnings - total_buy_in,
        "taxable_winnings": taxable_winnings,
        "tax_rate": cfg["tax_rate"],
        "tax_rate_percent": round(cfg["tax_rate"] * 100, 1),
        "tax_calculated": total_tax,
        "tax_amount": tax_amount,
        "cess_rate": cfg["cess_rate"],
        "cess_amount": cess_amount,
        "surcharge_rate": cfg["surcharge_rate"],
        "surcharge_amount": surcharge_amount,
        "total_tax": total_tax,
        "tds_rate": cfg["tds_rate"],
        "tds_deducted": tds_amount,
        "tds_amount": tds_amount,
        "balance_payable": balance_payable,
        "net_payout": net_payout,
        "effective_rate": round(total_tax / gross_winnings * 100, 2) if gross_winnings > 0 else 0,
        "disclaimer": cfg.get("disclaimer", ""),
    }


def calculate_game_tax(gross_winnings: float, buy_in: float = 0.0, tax_rate: float = 30.0) -> dict:
    """Calculate tax for a specific game winning amount."""
    rate_decimal = tax_rate / 100.0 if tax_rate > 1 else tax_rate
    tax_calc = calculate_tax(gross_winnings, config={"tax_rate": rate_decimal, "cess_rate": 0.04, "surcharge_rate": 0.0, "tds_rate": rate_decimal})
    tax_calc["buy_in"] = buy_in
    return tax_calc


def calculate_tds(gross_amount: float, tds_rate: float = None) -> dict:
    """Calculate TDS on a single winning amount."""
    rate = tds_rate or TAX_CONFIG["tds_rate"]
    tds_amount = round(gross_amount * rate, 2)
    net_payout = round(gross_amount - tds_amount, 2)

    return {
        "gross_amount": gross_amount,
        "tds_rate": rate,
        "tds_amount": tds_amount,
        "net_payout": net_payout,
    }


def get_tax_summary_for_individual(pan: str) -> dict:
    """Get comprehensive tax summary for an individual by PAN."""
    winnings = execute_query(
        """
        SELECT COALESCE(SUM(wa.gross_winning), 0) as total_winnings
        FROM winning_allocations wa
        JOIN individuals i ON wa.individual_id = i.individual_id
        WHERE i.pan = ?
        """,
        (pan,),
    )
    total_winnings = winnings[0]["total_winnings"] if winnings else 0

    tds = execute_query(
        """
        SELECT COALESCE(SUM(tds_amount), 0) as total_tds,
               COUNT(*) as num_records
        FROM tds_records
        WHERE pan = ?
        """,
        (pan,),
    )

    tax_calc = calculate_tax(total_winnings)
    tax_calc["actual_tds_deducted"] = tds[0]["total_tds"] if tds else 0
    tax_calc["tds_records_count"] = tds[0]["num_records"] if tds else 0

    return tax_calc


def get_aggregate_tax_stats():
    """Get aggregate tax statistics for the dashboard."""
    return execute_query(
        """
        SELECT
            COUNT(*) as total_calculations,
            SUM(gross_winnings) as total_gross_winnings,
            SUM(total_tax) as total_tax_liability,
            SUM(tds_deducted) as total_tds_deducted,
            SUM(balance_payable) as total_balance_payable,
            AVG(gross_winnings) as avg_winnings
        FROM tax_calculations
        """
    )
