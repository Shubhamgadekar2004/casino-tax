"""
Casino Model — data access for casinos and casino_accounts tables.
"""
from database.database import execute_query


def get_all_casinos():
    return execute_query("SELECT * FROM casinos ORDER BY casino_id")


def get_casino_by_id(casino_id: str):
    rows = execute_query("SELECT * FROM casinos WHERE casino_id = ?", (casino_id,))
    return rows[0] if rows else None


def get_accounts_for_individual(individual_id: str):
    return execute_query(
        """
        SELECT ca.*, c.name as casino_name
        FROM casino_accounts ca
        JOIN casinos c ON ca.casino_id = c.casino_id
        WHERE ca.individual_id = ?
        """,
        (individual_id,),
    )


def get_all_accounts():
    return execute_query(
        """
        SELECT ca.*, i.first_name, i.last_name, i.pan, c.name as casino_name
        FROM casino_accounts ca
        JOIN individuals i ON ca.individual_id = i.individual_id
        JOIN casinos c ON ca.casino_id = c.casino_id
        ORDER BY ca.account_id
        """
    )
