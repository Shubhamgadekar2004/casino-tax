"""
Audit Service — immutable audit trail for all administrative actions.
"""
import uuid
from datetime import datetime
from database.database import get_connection, execute_query


def log_action(
    user: str,
    action: str,
    entity: str,
    entity_id: str = None,
    old_value: str = None,
    new_value: str = None,
    description: str = None,
):
    """Record an audit trail entry."""
    conn = get_connection()
    try:
        audit_id = f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            """
            INSERT INTO audit_logs
            (audit_id, user_id, action, entity, entity_id,
             old_value, new_value, ip_address, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (audit_id, user, action, entity, entity_id,
             old_value, new_value, "DEMO", description),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_logs(limit: int = 100):
    """Get the most recent audit log entries."""
    return execute_query(
        "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )


def get_logs_by_entity(entity: str, entity_id: str = None):
    """Get audit logs for a specific entity."""
    if entity_id:
        return execute_query(
            "SELECT * FROM audit_logs WHERE entity = ? AND entity_id = ? ORDER BY timestamp DESC",
            (entity, entity_id),
        )
    return execute_query(
        "SELECT * FROM audit_logs WHERE entity = ? ORDER BY timestamp DESC",
        (entity,),
    )


def get_logs_by_user(user: str):
    """Get audit logs for a specific user."""
    return execute_query(
        "SELECT * FROM audit_logs WHERE user_id = ? ORDER BY timestamp DESC",
        (user,),
    )


def get_audit_summary():
    """Get summary statistics for audit logs."""
    return execute_query(
        """
        SELECT
            COUNT(*) as total_entries,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT entity) as unique_entities,
            COUNT(DISTINCT action) as unique_actions,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM audit_logs
        """
    )
