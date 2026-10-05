"""
Game Service — business logic for game operations.
"""
from models.game import (
    get_all_games, get_game_by_id, get_game_participants,
    get_game_winners, get_game_summary,
)
from database.database import execute_query


def get_game_explorer_data(game_id: str):
    """Get complete game data for the Game Explorer view."""
    summary = get_game_summary(game_id)
    if not summary:
        return None

    game = summary["game"]
    player_table = summary["player_table"]

    # Determine scenario type
    if game["num_winners"] == 0:
        scenario = "No Winner"
    elif game["num_winners"] == 1:
        scenario = "Single Winner"
    else:
        scenario = f"{game['num_winners']} Shared Winners"

    return {
        **summary,
        "scenario": scenario,
        "allocation_method": game["allocation_method"],
    }


def get_game_statistics():
    """Get aggregate game statistics."""
    stats = execute_query(
        """
        SELECT
            COUNT(*) as total_games,
            SUM(prize_pool) as total_prize_pool,
            AVG(prize_pool) as avg_prize_pool,
            SUM(num_participants) as total_participations,
            SUM(num_winners) as total_winners,
            COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_games,
            COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) as cancelled_games
        FROM games
        """
    )
    return stats[0] if stats else {}


def get_game_type_distribution():
    """Get distribution of games by type."""
    return execute_query(
        """
        SELECT game_type,
               COUNT(*) as count,
               SUM(prize_pool) as total_pool,
               AVG(prize_pool) as avg_pool
        FROM games
        GROUP BY game_type
        ORDER BY count DESC
        """
    )


def validate_winning_allocation(game_id: str) -> dict:
    """Validate that winning allocations match the game's distributable prize."""
    game = get_game_by_id(game_id)
    if not game:
        return {"valid": False, "error": "Game not found"}

    if game["num_winners"] == 0:
        return {"valid": True, "message": "No winners — no allocation to validate"}

    allocations = execute_query(
        "SELECT * FROM winning_allocations WHERE game_id = ?", (game_id,)
    )

    total_allocated = sum(a["gross_winning"] for a in allocations)
    pool = game["prize_pool"]

    # For FIXED_AMOUNT, total may not equal pool exactly
    if game["allocation_method"] == "FIXED_AMOUNT":
        if total_allocated <= pool:
            return {
                "valid": True,
                "total_allocated": total_allocated,
                "prize_pool": pool,
                "message": "Fixed allocation within prize pool",
            }
        else:
            return {
                "valid": False,
                "total_allocated": total_allocated,
                "prize_pool": pool,
                "error": f"Allocation ₹{total_allocated:,.2f} exceeds prize pool ₹{pool:,.2f}",
            }

    # For percentage / equal share, must equal prize pool (with rounding tolerance)
    if abs(total_allocated - pool) < 1.0:
        return {
            "valid": True,
            "total_allocated": total_allocated,
            "prize_pool": pool,
            "message": "Allocation matches prize pool",
        }
    else:
        return {
            "valid": False,
            "total_allocated": total_allocated,
            "prize_pool": pool,
            "error": (
                f"Accounting exception: sum of allocations (₹{total_allocated:,.2f}) "
                f"!= distributable prize (₹{pool:,.2f})"
            ),
        }
