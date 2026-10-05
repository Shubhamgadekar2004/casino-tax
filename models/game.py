"""
Game Model — data access for games and game_participants tables.
"""
from database.database import execute_query


def get_all_games():
    return execute_query("SELECT * FROM games ORDER BY game_date DESC")


def get_game_by_id(game_id: str):
    rows = execute_query("SELECT * FROM games WHERE game_id = ?", (game_id,))
    return rows[0] if rows else None


def get_game_participants(game_id: str):
    return execute_query(
        """
        SELECT gp.*, i.first_name, i.last_name, i.pan
        FROM game_participants gp
        JOIN individuals i ON gp.individual_id = i.individual_id
        WHERE gp.game_id = ?
        ORDER BY gp.position
        """,
        (game_id,),
    )


def get_game_winners(game_id: str):
    return execute_query(
        """
        SELECT gp.*, i.first_name, i.last_name, i.pan,
               wa.gross_winning, wa.share_percentage, wa.allocation_method
        FROM game_participants gp
        JOIN individuals i ON gp.individual_id = i.individual_id
        LEFT JOIN winning_allocations wa
            ON wa.game_id = gp.game_id AND wa.individual_id = gp.individual_id
        WHERE gp.game_id = ? AND gp.is_winner = 1
        """,
        (game_id,),
    )


def get_game_summary(game_id: str):
    game = get_game_by_id(game_id)
    if not game:
        return None
    participants = get_game_participants(game_id)
    winners = get_game_winners(game_id)

    # Build player table
    player_table = []
    for p in participants:
        winning = next(
            (w["gross_winning"] for w in winners
             if w["individual_id"] == p["individual_id"]),
            0,
        )
        player_table.append({
            "player": f"{p['first_name']} {p['last_name']}",
            "pan": p["pan"],
            "buy_in": p["buy_in_amount"],
            "winning": winning,
            "net": winning - p["buy_in_amount"],
            "is_winner": bool(p["is_winner"]),
        })

    return {
        "game": game,
        "participants": participants,
        "winners": winners,
        "player_table": player_table,
        "total_buyin": sum(p["buy_in_amount"] for p in participants),
        "total_winning": sum(w["gross_winning"] for w in winners),
    }


def get_games_by_type(game_type: str):
    return execute_query(
        "SELECT * FROM games WHERE game_type = ? ORDER BY game_date DESC",
        (game_type,),
    )


def get_games_for_individual(individual_id: str):
    return execute_query(
        """
        SELECT g.*, gp.buy_in_amount, gp.is_winner
        FROM games g
        JOIN game_participants gp ON g.game_id = gp.game_id
        WHERE gp.individual_id = ?
        ORDER BY g.game_date DESC
        """,
        (individual_id,),
    )
