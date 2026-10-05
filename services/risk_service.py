"""
Risk Service — transparent rule-based risk scoring engine.
Every score has visible contributing factors — no black-box scoring.
"""
from database.database import execute_query
from config.settings import RISK_RULES, RISK_THRESHOLDS


def calculate_risk_score(pan_or_id: str) -> dict:
    """
    Calculate a transparent risk score for an individual by PAN or individual_id.
    """
    ind = execute_query(
        "SELECT * FROM individuals WHERE individual_id = ? OR pan = ?",
        (pan_or_id, pan_or_id),
    )
    if not ind:
        return {"error": "Individual not found"}
    ind = ind[0]
    pan = ind["pan"]
    ind_id = ind["individual_id"]

    winnings = execute_query(
        """
        SELECT COALESCE(SUM(wa.gross_winning), 0) as total
        FROM winning_allocations wa
        WHERE wa.individual_id = ?
        """,
        (ind_id,),
    )
    casino_winnings = winnings[0]["total"] if winnings else 0

    itr = execute_query(
        "SELECT * FROM itr_records WHERE pan = ? ORDER BY assessment_year DESC LIMIT 1",
        (pan,),
    )
    declared = itr[0]["casino_winnings_declared"] if itr else 0

    txn_stats = execute_query(
        """
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE pan = ? AND transaction_type = 'WINNING'
        """,
        (pan,),
    )

    score = 0
    factors = []
    rules_applied = []

    if casino_winnings > 0 and declared == 0:
        points = RISK_RULES["winnings_not_reported"]
        score += points
        factors.append(f"₹{casino_winnings:,.0f} casino winnings not declared in ITR (+{points})")
        rules_applied.append("winnings_not_reported")

    if casino_winnings > 0 and 0 < declared < casino_winnings:
        diff = casino_winnings - declared
        if diff > 50000:
            points = RISK_RULES["large_under_reporting"]
            score += points
            factors.append(
                f"₹{diff:,.0f} under-reported "
                f"(casino: ₹{casino_winnings:,.0f}, ITR: ₹{declared:,.0f}) (+{points})"
            )
            rules_applied.append("large_under_reporting")

    recon = execute_query(
        "SELECT * FROM reconciliations WHERE pan = ? AND status NOT IN ('MATCH')",
        (pan,),
    )
    if len(recon) > 0:
        points = RISK_RULES["repeated_mismatches"]
        score += points
        factors.append(f"Reconciliation mismatch detected ({recon[0].get('status', 'N/A')}) (+{points})")
        rules_applied.append("repeated_mismatches")

    if casino_winnings > 200000:
        points = RISK_RULES["large_cash_activity"]
        score += points
        factors.append(f"High-value casino activity: ₹{casino_winnings:,.0f} (+{points})")
        rules_applied.append("large_cash_activity")

    if txn_stats and txn_stats[0]["count"] > 3:
        points = RISK_RULES["frequent_high_value_txns"]
        score += points
        factors.append(
            f"{txn_stats[0]['count']} winning transactions "
            f"totalling ₹{txn_stats[0]['total']:,.0f} (+{points})"
        )
        rules_applied.append("frequent_high_value_txns")

    score = min(score, 100)

    risk_level = "LOW"
    for level, (lo, hi) in RISK_THRESHOLDS.items():
        if lo <= score <= hi:
            risk_level = level
            break

    if not factors:
        factors.append("No significant risk factors identified")

    return {
        "individual_id": ind_id,
        "pan": pan,
        "individual": f"{ind['first_name']} {ind['last_name']}",
        "risk_score": score,
        "score": score,
        "risk_tier": risk_level.lower(),
        "risk_level": risk_level,
        "risk_factors": factors,
        "factors": factors,
        "rules_applied": rules_applied,
        "casino_winnings": casino_winnings,
        "itr_declared": declared,
        "difference": casino_winnings - declared,
    }


def get_high_risk_individuals():
    """Get individuals with HIGH or CRITICAL risk."""
    return execute_query(
        """
        SELECT rs.*, i.first_name, i.last_name
        FROM risk_scores rs
        JOIN individuals i ON rs.individual_id = i.individual_id
        WHERE rs.risk_level IN ('HIGH', 'CRITICAL')
        ORDER BY rs.score DESC
        """
    )


def get_risk_level_summary():
    """Get count by risk level for dashboard."""
    return execute_query(
        """
        SELECT risk_level, COUNT(*) as count
        FROM risk_scores
        GROUP BY risk_level
        """
    )
