"""
Reconciliation Model — data access for reconciliations, ITR, and risk scores.
"""
from database.database import execute_query


def get_all_reconciliations():
    return execute_query(
        """
        SELECT r.*, i.first_name, i.last_name
        FROM reconciliations r
        JOIN individuals i ON r.individual_id = i.individual_id
        ORDER BY r.difference DESC
        """
    )


def get_reconciliation_by_pan(pan: str):
    rows = execute_query(
        "SELECT * FROM reconciliations WHERE pan = ?", (pan,)
    )
    return rows[0] if rows else None


def get_reconciliation_by_status(status: str):
    return execute_query(
        """
        SELECT r.*, i.first_name, i.last_name
        FROM reconciliations r
        JOIN individuals i ON r.individual_id = i.individual_id
        WHERE r.status = ?
        ORDER BY r.difference DESC
        """,
        (status,),
    )


def get_itr_records():
    return execute_query(
        """
        SELECT itr.*, i.first_name, i.last_name
        FROM itr_records itr
        JOIN individuals i ON itr.individual_id = i.individual_id
        ORDER BY itr.itr_id
        """
    )


def get_itr_by_pan(pan: str):
    rows = execute_query(
        "SELECT * FROM itr_records WHERE pan = ?", (pan,)
    )
    return rows[0] if rows else None


def get_all_risk_scores():
    return execute_query(
        """
        SELECT rs.*, i.first_name, i.last_name
        FROM risk_scores rs
        JOIN individuals i ON rs.individual_id = i.individual_id
        ORDER BY rs.score DESC
        """
    )


def get_risk_score_by_pan(pan: str):
    rows = execute_query(
        """
        SELECT rs.*, i.first_name, i.last_name
        FROM risk_scores rs
        JOIN individuals i ON rs.individual_id = i.individual_id
        WHERE rs.pan = ?
        """,
        (pan,),
    )
    return rows[0] if rows else None


def get_risk_distribution():
    return execute_query(
        """
        SELECT risk_level, COUNT(*) as count
        FROM risk_scores
        GROUP BY risk_level
        ORDER BY
            CASE risk_level
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
            END
        """
    )


def get_audit_logs(limit=200):
    return execute_query(
        "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )


def get_audit_logs_by_entity(entity: str):
    return execute_query(
        "SELECT * FROM audit_logs WHERE entity = ? ORDER BY timestamp DESC",
        (entity,),
    )
