"""
Transaction Model — data access for the transactions ledger.
"""
from database.database import execute_query


def get_all_transactions(limit=500):
    return execute_query(
        "SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT ?",
        (limit,),
    )


def get_transactions_by_pan(pan: str):
    return execute_query(
        "SELECT * FROM transactions WHERE pan = ? ORDER BY transaction_date DESC",
        (pan,),
    )


def get_transactions_by_game(game_id: str):
    return execute_query(
        "SELECT * FROM transactions WHERE game_id = ? ORDER BY transaction_date",
        (game_id,),
    )


def get_transactions_by_type(txn_type: str):
    return execute_query(
        "SELECT * FROM transactions WHERE transaction_type = ? ORDER BY transaction_date DESC",
        (txn_type,),
    )


def get_transaction_summary():
    return execute_query(
        """
        SELECT transaction_type,
               COUNT(*) as count,
               SUM(amount) as total_amount,
               AVG(amount) as avg_amount,
               credit_debit
        FROM transactions
        GROUP BY transaction_type, credit_debit
        ORDER BY transaction_type
        """
    )


def get_transactions_by_date_range(start_date: str, end_date: str):
    return execute_query(
        """
        SELECT * FROM transactions
        WHERE DATE(transaction_date) BETWEEN ? AND ?
        ORDER BY transaction_date DESC
        """,
        (start_date, end_date),
    )


def get_individual_ledger(pan: str):
    """Get the full ledger for an individual by PAN."""
    transactions = get_transactions_by_pan(pan)

    summary = {
        "BUY_IN": 0,
        "GAME_ENTRY": 0,
        "WINNING": 0,
        "REDEMPTION": 0,
        "REFUND": 0,
        "ADJUSTMENT": 0,
        "TDS": 0,
    }

    for txn in transactions:
        tt = txn["transaction_type"]
        if tt in summary:
            summary[tt] += txn["amount"]

    return {
        "transactions": transactions,
        "summary": summary,
        "net_result": summary["WINNING"] - summary["BUY_IN"],
        "total_credits": summary["WINNING"] + summary["REFUND"],
        "total_debits": summary["BUY_IN"] + summary["TDS"] + summary["REDEMPTION"],
    }


def get_player_ledger(individual_id: str) -> list:
    """Get list of transaction records for an individual_id or PAN."""
    # Lookup PAN if individual_id is provided
    ind = execute_query("SELECT pan FROM individuals WHERE individual_id = ?", (individual_id,))
    pan = ind[0]["pan"] if ind else individual_id

    txs = get_transactions_by_pan(pan)

    # Normalize fields for reports/pages
    normalized = []
    for t in txs:
        normalized.append({
            "transaction_id": t.get("transaction_id", ""),
            "timestamp": t.get("transaction_date", ""),
            "game_name": t.get("casino_name", "Casino Session"),
            "buy_in_amount": t.get("amount", 0.0) if t.get("transaction_type") == "BUY_IN" else 0.0,
            "payout_amount": t.get("amount", 0.0) if t.get("transaction_type") == "WINNING" else 0.0,
            "tds_deducted": t.get("amount", 0.0) if t.get("transaction_type") == "TDS" else 0.0,
            "transaction_type": t.get("transaction_type", "OTHER"),
        })

    return normalized
