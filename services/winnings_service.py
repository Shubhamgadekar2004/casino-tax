"""
Winnings Service — winning allocation engine.
Supports single winner, equal share, percentage-based, fixed amount, and no winner.
"""
from database.database import execute_query


def allocate_winnings(game_id: str, prize_pool: float, participants: list, rule: str = "EQUAL_SPLIT") -> list:
    """
    Allocate prize pool among participants according to specified rule.
    Rules: EQUAL_SPLIT, PROPORTIONAL_BUYIN, WINNER_TAKES_ALL, RANKED_TIER
    """
    if not participants or prize_pool <= 0:
        return []

    count = len(participants)
    allocations = []

    if rule == "EQUAL_SPLIT":
        per_share = prize_pool / count
        for p in participants:
            allocations.append({
                "game_id": game_id,
                "participant_id": p.get("participant_id"),
                "individual_id": p.get("individual_id"),
                "allocated_amount": round(per_share, 2),
                "rule": rule,
            })

    elif rule == "PROPORTIONAL_BUYIN":
        total_buyin = sum(p.get("buy_in", 0) for p in participants)
        if total_buyin == 0:
            total_buyin = 1.0
        for p in participants:
            share = (p.get("buy_in", 0) / total_buyin) * prize_pool
            allocations.append({
                "game_id": game_id,
                "participant_id": p.get("participant_id"),
                "individual_id": p.get("individual_id"),
                "allocated_amount": round(share, 2),
                "rule": rule,
            })

    elif rule == "WINNER_TAKES_ALL":
        for i, p in enumerate(participants):
            amount = prize_pool if i == 0 else 0.0
            allocations.append({
                "game_id": game_id,
                "participant_id": p.get("participant_id"),
                "individual_id": p.get("individual_id"),
                "allocated_amount": round(amount, 2),
                "rule": rule,
            })

    else:
        # Default / Ranked Tier (50%, 30%, 20% etc.)
        percentages = [0.50, 0.30, 0.20]
        for i, p in enumerate(participants):
            pct = percentages[i] if i < len(percentages) else 0.0
            allocations.append({
                "game_id": game_id,
                "participant_id": p.get("participant_id"),
                "individual_id": p.get("individual_id"),
                "allocated_amount": round(prize_pool * pct, 2),
                "rule": rule,
            })

    return allocations


def calculate_winnings(game_id: str) -> dict:
    """
    Calculate and validate winning allocations for a game.

    Returns:
        dict with keys: game_id, allocations, total_allocated, prize_pool, valid, message
    """
    game = execute_query("SELECT * FROM games WHERE game_id = ?", (game_id,))
    if not game:
        return {"valid": False, "error": "Game not found"}
    game = game[0]

    if game["num_winners"] == 0:
        return {
            "game_id": game_id,
            "allocations": [],
            "total_allocated": 0,
            "prize_pool": game["prize_pool"],
            "valid": True,
            "message": _get_no_winner_treatment(game),
        }

    allocations = execute_query(
        """
        SELECT wa.*, i.first_name, i.last_name, i.pan
        FROM winning_allocations wa
        JOIN individuals i ON wa.individual_id = i.individual_id
        WHERE wa.game_id = ?
        """,
        (game_id,),
    )

    total_allocated = sum(a["gross_winning"] for a in allocations)
    pool = game["prize_pool"]

    # Validate
    if game["allocation_method"] == "FIXED_AMOUNT":
        valid = total_allocated <= pool
    else:
        valid = abs(total_allocated - pool) < 1.0

    return {
        "game_id": game_id,
        "allocations": allocations,
        "total_allocated": total_allocated,
        "prize_pool": pool,
        "valid": valid,
        "allocation_method": game["allocation_method"],
        "message": "Allocation verified" if valid else "ACCOUNTING EXCEPTION: allocation mismatch",
    }


def _get_no_winner_treatment(game: dict) -> str:
    """Get the treatment description for no-winner games."""
    status = game.get("status", "")
    desc = game.get("description", "")

    if status == "CANCELLED":
        return "Game cancelled — buy-ins may be refunded"
    elif "rollover" in desc.lower():
        return "Prize pool rolled over to next game"
    elif "retained" in desc.lower():
        return "Prize pool retained by casino"
    else:
        return "No winner — non-winning game transaction recorded"


def get_winnings_by_individual():
    """Get total winnings per individual."""
    return execute_query(
        """
        SELECT i.individual_id, i.first_name, i.last_name, i.pan,
               COALESCE(SUM(wa.gross_winning), 0) as total_winnings,
               COUNT(wa.allocation_id) as games_won
        FROM individuals i
        LEFT JOIN winning_allocations wa ON i.individual_id = wa.individual_id
        GROUP BY i.individual_id
        ORDER BY total_winnings DESC
        """
    )


def get_single_vs_shared_stats():
    """Get statistics on single vs shared winnings."""
    return execute_query(
        """
        SELECT allocation_method,
               COUNT(*) as count,
               SUM(gross_winning) as total_amount
        FROM winning_allocations
        GROUP BY allocation_method
        """
    )
