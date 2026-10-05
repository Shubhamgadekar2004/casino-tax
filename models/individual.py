"""
Individual Model — data access for individuals table.
"""
from database.database import execute_query, get_connection


def get_all_individuals():
    return execute_query("SELECT * FROM individuals ORDER BY individual_id")


def get_individual_by_id(individual_id: str):
    rows = execute_query(
        "SELECT * FROM individuals WHERE individual_id = ?", (individual_id,)
    )
    return rows[0] if rows else None


def get_individual_by_pan(pan: str):
    rows = execute_query("SELECT * FROM individuals WHERE pan = ?", (pan,))
    return rows[0] if rows else None


def get_individual_summary(individual_id: str):
    """Get a comprehensive summary for an individual."""
    ind = get_individual_by_id(individual_id)
    if not ind:
        return None

    # Get casino account
    accounts = execute_query(
        "SELECT * FROM casino_accounts WHERE individual_id = ?",
        (individual_id,),
    )

    # Get games played
    games = execute_query(
        """
        SELECT gp.*, g.game_type, g.game_date, g.prize_pool, g.status as game_status
        FROM game_participants gp
        JOIN games g ON gp.game_id = g.game_id
        WHERE gp.individual_id = ?
        ORDER BY g.game_date DESC
        """,
        (individual_id,),
    )

    # Get winnings
    winnings = execute_query(
        """
        SELECT wa.*, g.game_type, g.game_date
        FROM winning_allocations wa
        JOIN games g ON wa.game_id = g.game_id
        WHERE wa.individual_id = ?
        """,
        (individual_id,),
    )

    # Get transactions
    transactions = execute_query(
        "SELECT * FROM transactions WHERE pan = ? ORDER BY transaction_date DESC",
        (ind["pan"],),
    )

    # Aggregates
    total_buyins = sum(g["buy_in_amount"] for g in games)
    total_winnings = sum(w["gross_winning"] for w in winnings)
    total_tds = sum(
        t["amount"] for t in transactions if t["transaction_type"] == "TDS"
    )
    total_redemptions = sum(
        t["amount"] for t in transactions if t["transaction_type"] == "REDEMPTION"
    )

    return {
        "individual": ind,
        "accounts": accounts,
        "games": games,
        "winnings": winnings,
        "transactions": transactions,
        "totals": {
            "total_buyins": total_buyins,
            "total_winnings": total_winnings,
            "total_tds": total_tds,
            "total_redemptions": total_redemptions,
            "net_result": total_winnings - total_buyins,
            "games_played": len(games),
            "games_won": len(winnings),
        },
    }


def search_individuals(search_term: str):
    return execute_query(
        """
        SELECT * FROM individuals
        WHERE pan LIKE ? OR first_name LIKE ? OR last_name LIKE ?
        ORDER BY individual_id
        """,
        (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"),
    )
