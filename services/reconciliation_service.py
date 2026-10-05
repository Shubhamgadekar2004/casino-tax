"""
Reconciliation Service — compares casino records with ITR declarations.
"""
from database.database import execute_query
from config.settings import TAX_CONFIG


def reconcile_individual(pan_or_id: str, declared_winnings: float = None) -> dict:
    """
    Reconcile an individual's casino records against ITR declaration.
    Accepts either individual_id or PAN.
    """
    ind = execute_query(
        "SELECT * FROM individuals WHERE individual_id = ? OR pan = ?",
        (pan_or_id, pan_or_id),
    )
    if ind:
        pan = ind[0]["pan"]
        ind_id = ind[0]["individual_id"]
    else:
        pan = pan_or_id
        ind_id = pan_or_id

    # Get casino winnings
    winnings = execute_query(
        """
        SELECT COALESCE(SUM(wa.gross_winning), 0) as casino_winnings
        FROM winning_allocations wa
        WHERE wa.individual_id = ?
        """,
        (ind_id,),
    )
    casino_winnings = winnings[0]["casino_winnings"] if winnings else 0

    # Get TDS records
    tds = execute_query(
        "SELECT COALESCE(SUM(tds_amount), 0) as total_tds FROM tds_records WHERE pan = ?",
        (pan,),
    )
    total_tds = tds[0]["total_tds"] if tds else 0

    # Get ITR declaration
    if declared_winnings is None:
        itr = execute_query(
            "SELECT * FROM itr_records WHERE pan = ? ORDER BY assessment_year DESC LIMIT 1",
            (pan,),
        )
        itr_record = itr[0] if itr else None
        declared = itr_record["casino_winnings_declared"] if itr_record else 0
        reported_tax = itr_record["tax_paid"] if itr_record else 0
    else:
        itr_record = None
        declared = float(declared_winnings)
        reported_tax = declared * 0.30

    expected_tax = round(
        casino_winnings * TAX_CONFIG["tax_rate"] * (1 + TAX_CONFIG["cess_rate"]), 2
    )

    difference = round(casino_winnings - declared, 2)

    if casino_winnings == 0 and declared == 0:
        status = "MATCH"
    elif abs(difference) < 1:
        status = "MATCH"
    elif declared == 0 and casino_winnings > 0:
        status = "NOT-REPORTED"
    elif difference > 0:
        if difference > casino_winnings * 0.1:
            status = "UNDER-REPORTED"
        else:
            status = "REVIEW"
    elif difference < 0:
        status = "OVER-REPORTED"
    else:
        status = "REVIEW"

    return {
        "individual_id": ind_id,
        "pan": pan,
        "casino_winnings": casino_winnings,
        "itr_declared_winnings": declared,
        "declared_winnings": declared,
        "discrepancy": difference,
        "difference": difference,
        "tds_deducted": total_tds,
        "expected_tax": expected_tax,
        "reported_tax": reported_tax,
        "status": status,
        "itr_record": itr_record,
    }


def reconcile_all() -> list:
    """Reconcile all individuals."""
    individuals = execute_query("SELECT pan FROM individuals ORDER BY individual_id")
    results = []
    for ind in individuals:
        result = reconcile_individual(ind["pan"])
        results.append(result)
    return results


def get_reconciliation_summary():
    """Get aggregate reconciliation statistics."""
    return execute_query(
        """
        SELECT status,
               COUNT(*) as count,
               SUM(ABS(difference)) as total_difference,
               AVG(ABS(difference)) as avg_difference
        FROM reconciliations
        GROUP BY status
        ORDER BY count DESC
        """
    )
