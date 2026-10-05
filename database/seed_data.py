"""
Synthetic Data Generator for Casino Tax Demo
Generates 20 individuals, 20 games, 100+ transactions, and all supporting records.
All data is synthetic — no real PAN numbers or personal information.
"""
import uuid
import random
import json
from datetime import datetime, timedelta
from faker import Faker

from database.database import get_connection, init_database
from config.settings import (
    CASINO_NAMES, GAME_TYPES, TAX_CONFIG,
    RISK_RULES, RISK_THRESHOLDS,
)

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)


def generate_uuid():
    return str(uuid.uuid4())[:8].upper()


def seed_all():
    """Main entry point — seed everything."""
    init_database()
    conn = get_connection()
    try:
        # Check if already seeded
        count = conn.execute("SELECT COUNT(*) FROM individuals").fetchone()[0]
        if count >= 20:
            return  # Already seeded

        casinos = seed_casinos(conn)
        individuals = seed_individuals(conn)
        accounts = seed_casino_accounts(conn, individuals, casinos)
        games = seed_games(conn, casinos)
        participants = seed_game_participants(conn, games, individuals)
        allocations = seed_winning_allocations(conn, games, participants)
        seed_transactions(conn, individuals, games, participants, allocations)
        seed_tax_configuration(conn)
        tds_records = seed_tds_records(conn, allocations, individuals)
        seed_tax_calculations(conn, individuals, allocations, tds_records)
        itr_records = seed_itr_records(conn, individuals, allocations)
        seed_reconciliations(conn, individuals, allocations, itr_records, tds_records)
        seed_risk_scores(conn, individuals, allocations, itr_records)
        seed_audit_logs(conn)
        conn.commit()

        # Export CSVs
        export_csvs(conn)
    finally:
        conn.close()


# ─── Casinos ──────────────────────────────────────────────────────────
def seed_casinos(conn):
    casinos = []
    for i, name in enumerate(CASINO_NAMES):
        casino = {
            "casino_id": f"CAS-{i+1:03d}",
            "name": name,
            "location": fake.city(),
            "license_number": f"LIC-DEMO-{i+1:04d}",
            "status": "ACTIVE",
        }
        casinos.append(casino)
        conn.execute(
            "INSERT INTO casinos (casino_id, name, location, license_number, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (casino["casino_id"], casino["name"], casino["location"],
             casino["license_number"], casino["status"]),
        )
    return casinos


# ─── Individuals ──────────────────────────────────────────────────────
def seed_individuals(conn):
    individuals = []
    kyc_statuses = ["VERIFIED", "VERIFIED", "VERIFIED", "PENDING", "VERIFIED"]

    for i in range(1, 21):
        reg_date = fake.date_between(start_date="-2y", end_date="-6m")
        ind = {
            "individual_id": f"IND-{i:03d}",
            "pan": f"TEST{i:04d}X",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "mobile": fake.phone_number()[:10],
            "date_of_birth": fake.date_of_birth(minimum_age=21, maximum_age=65).isoformat(),
            "kyc_status": kyc_statuses[i % len(kyc_statuses)],
            "kyc_date": (reg_date + timedelta(days=random.randint(1, 30))).isoformat()
                        if kyc_statuses[i % len(kyc_statuses)] == "VERIFIED" else None,
            "registration_date": reg_date.isoformat(),
            "risk_score": 0,
            "status": "ACTIVE",
        }
        individuals.append(ind)
        conn.execute(
            "INSERT INTO individuals "
            "(individual_id, pan, first_name, last_name, email, mobile, "
            "date_of_birth, kyc_status, kyc_date, registration_date, risk_score, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ind["individual_id"], ind["pan"], ind["first_name"], ind["last_name"],
             ind["email"], ind["mobile"], ind["date_of_birth"], ind["kyc_status"],
             ind["kyc_date"], ind["registration_date"], ind["risk_score"], ind["status"]),
        )
    return individuals


# ─── Casino Accounts ──────────────────────────────────────────────────
def seed_casino_accounts(conn, individuals, casinos):
    accounts = []
    for ind in individuals:
        casino = random.choice(casinos)
        acc = {
            "account_id": f"ACC-{ind['individual_id'].split('-')[1]}",
            "individual_id": ind["individual_id"],
            "casino_id": casino["casino_id"],
            "account_number": f"CA-{generate_uuid()}",
            "balance": round(random.uniform(0, 50000), 2),
            "status": "ACTIVE",
            "opened_date": ind["registration_date"],
        }
        accounts.append(acc)
        conn.execute(
            "INSERT INTO casino_accounts "
            "(account_id, individual_id, casino_id, account_number, balance, status, opened_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (acc["account_id"], acc["individual_id"], acc["casino_id"],
             acc["account_number"], acc["balance"], acc["status"], acc["opened_date"]),
        )
    return accounts


# ─── Games ────────────────────────────────────────────────────────────
def seed_games(conn, casinos):
    """Create exactly 20 games covering all required scenarios."""
    games = []

    # Define the 20 game scenarios
    scenarios = [
        # Scenario A: Single Winner (Games 1–5)
        {"game_num": 1, "type": "Roulette",        "pool": 100000, "winners": 1, "method": "SINGLE_WINNER",  "participants": 5,  "status": "COMPLETED", "desc": "Single winner — full prize"},
        {"game_num": 2, "type": "Blackjack",       "pool": 200000, "winners": 1, "method": "SINGLE_WINNER",  "participants": 6,  "status": "COMPLETED", "desc": "Single winner — large prize"},
        {"game_num": 3, "type": "Poker",            "pool": 75000,  "winners": 1, "method": "SINGLE_WINNER",  "participants": 4,  "status": "COMPLETED", "desc": "Single winner — poker"},
        {"game_num": 4, "type": "Baccarat",         "pool": 150000, "winners": 1, "method": "SINGLE_WINNER",  "participants": 8,  "status": "COMPLETED", "desc": "Single winner — baccarat"},
        {"game_num": 5, "type": "Slot Tournament",  "pool": 50000,  "winners": 1, "method": "SINGLE_WINNER",  "participants": 10, "status": "COMPLETED", "desc": "Single winner — slot tournament"},

        # Scenario B: Two Shared Winners (Games 6–8)
        {"game_num": 6, "type": "Roulette",        "pool": 100000, "winners": 2, "method": "EQUAL_SHARE",    "participants": 6,  "status": "COMPLETED", "desc": "Two shared winners — equal split"},
        {"game_num": 7, "type": "Poker",            "pool": 200000, "winners": 2, "method": "PERCENTAGE_BASED", "participants": 5, "status": "COMPLETED", "desc": "Two shared winners — 60/40 split"},
        {"game_num": 8, "type": "Blackjack",       "pool": 80000,  "winners": 2, "method": "EQUAL_SHARE",    "participants": 4,  "status": "COMPLETED", "desc": "Two shared winners — equal"},

        # Scenario C: Three Shared Winners (Games 9–11)
        {"game_num": 9, "type": "Poker",            "pool": 150000, "winners": 3, "method": "EQUAL_SHARE",    "participants": 8,  "status": "COMPLETED", "desc": "Three shared winners — equal split"},
        {"game_num": 10, "type": "Baccarat",        "pool": 300000, "winners": 3, "method": "PERCENTAGE_BASED", "participants": 6, "status": "COMPLETED", "desc": "Three shared winners — 50/30/20"},
        {"game_num": 11, "type": "Roulette",        "pool": 120000, "winners": 3, "method": "EQUAL_SHARE",    "participants": 7,  "status": "COMPLETED", "desc": "Three shared winners — equal"},

        # Scenario D: Four Shared Winners (Games 12–14)
        {"game_num": 12, "type": "Poker",            "pool": 200000, "winners": 4, "method": "EQUAL_SHARE",    "participants": 8,  "status": "COMPLETED", "desc": "Four shared winners — equal split"},
        {"game_num": 13, "type": "Slot Tournament",  "pool": 400000, "winners": 4, "method": "FIXED_AMOUNT",   "participants": 10, "status": "COMPLETED", "desc": "Four shared winners — fixed amounts"},
        {"game_num": 14, "type": "Blackjack",       "pool": 160000, "winners": 4, "method": "EQUAL_SHARE",    "participants": 6,  "status": "COMPLETED", "desc": "Four shared winners — equal"},

        # Scenario E: No Winner (Games 15–18)
        {"game_num": 15, "type": "Roulette",        "pool": 100000, "winners": 0, "method": "NO_WINNER",      "participants": 5,  "status": "COMPLETED",  "desc": "No winner — prize pool retained"},
        {"game_num": 16, "type": "Poker",            "pool": 80000,  "winners": 0, "method": "NO_WINNER",      "participants": 4,  "status": "CANCELLED",  "desc": "No winner — game cancelled"},
        {"game_num": 17, "type": "Baccarat",         "pool": 60000,  "winners": 0, "method": "NO_WINNER",      "participants": 6,  "status": "COMPLETED",  "desc": "No winner — rollover to next game"},
        {"game_num": 18, "type": "Slot Tournament",  "pool": 50000,  "winners": 0, "method": "NO_WINNER",      "participants": 3,  "status": "COMPLETED",  "desc": "No winner — demo non-winning txn"},

        # Mixed scenarios (Games 19–20)
        {"game_num": 19, "type": "Poker",            "pool": 500000, "winners": 2, "method": "PERCENTAGE_BASED", "participants": 10, "status": "COMPLETED", "desc": "High-value — two shared winners 70/30"},
        {"game_num": 20, "type": "Blackjack",       "pool": 250000, "winners": 1, "method": "SINGLE_WINNER",  "participants": 8,  "status": "COMPLETED", "desc": "Single winner — high stakes blackjack"},
    ]

    base_date = datetime(2024, 4, 1)
    for s in scenarios:
        game_date = base_date + timedelta(days=random.randint(0, 300))
        game = {
            "game_id": f"GAME-{s['game_num']:03d}",
            "casino_id": random.choice(casinos)["casino_id"],
            "game_type": s["type"],
            "game_date": game_date.date().isoformat(),
            "start_time": game_date.isoformat(),
            "end_time": (game_date + timedelta(hours=random.randint(1, 4))).isoformat(),
            "prize_pool": s["pool"],
            "num_participants": s["participants"],
            "num_winners": s["winners"],
            "allocation_method": s["method"],
            "status": s["status"],
            "description": s["desc"],
        }
        games.append(game)
        conn.execute(
            "INSERT INTO games "
            "(game_id, casino_id, game_type, game_date, start_time, end_time, "
            "prize_pool, num_participants, num_winners, allocation_method, status, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (game["game_id"], game["casino_id"], game["game_type"], game["game_date"],
             game["start_time"], game["end_time"], game["prize_pool"],
             game["num_participants"], game["num_winners"], game["allocation_method"],
             game["status"], game["description"]),
        )
    return games


# ─── Game Participants ────────────────────────────────────────────────
def seed_game_participants(conn, games, individuals):
    """Assign participants to each game (many-to-many)."""
    all_participants = []

    for game in games:
        n = game["num_participants"]
        # Pick n random individuals (without replacement within a game)
        chosen = random.sample(individuals, min(n, len(individuals)))
        buy_in = round(game["prize_pool"] / n, 2) if n > 0 else 0

        for idx, ind in enumerate(chosen):
            part = {
                "participant_id": f"PART-{game['game_id'].split('-')[1]}-{idx+1:02d}",
                "game_id": game["game_id"],
                "individual_id": ind["individual_id"],
                "buy_in_amount": buy_in,
                "entry_time": game["start_time"],
                "exit_time": game["end_time"],
                "is_winner": 0,  # updated later
                "position": idx + 1,
                "status": "ACTIVE",
            }
            all_participants.append(part)
            conn.execute(
                "INSERT INTO game_participants "
                "(participant_id, game_id, individual_id, buy_in_amount, "
                "entry_time, exit_time, is_winner, position, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (part["participant_id"], part["game_id"], part["individual_id"],
                 part["buy_in_amount"], part["entry_time"], part["exit_time"],
                 part["is_winner"], part["position"], part["status"]),
            )
    return all_participants


# ─── Winning Allocations ─────────────────────────────────────────────
def seed_winning_allocations(conn, games, participants):
    """Create winning allocations for each game."""
    allocations = []

    for game in games:
        if game["num_winners"] == 0:
            continue  # No winner scenario

        game_parts = [p for p in participants if p["game_id"] == game["game_id"]]
        if not game_parts:
            continue

        winners = game_parts[:game["num_winners"]]
        pool = game["prize_pool"]

        for idx, winner in enumerate(winners):
            # Calculate share
            if game["allocation_method"] == "SINGLE_WINNER":
                share_pct = 100.0
                gross = pool
            elif game["allocation_method"] == "EQUAL_SHARE":
                share_pct = round(100.0 / game["num_winners"], 2)
                gross = round(pool / game["num_winners"], 2)
            elif game["allocation_method"] == "PERCENTAGE_BASED":
                # Define custom percentages
                if game["num_winners"] == 2:
                    pcts = [60, 40] if game["game_id"] == "GAME-007" else [70, 30]
                elif game["num_winners"] == 3:
                    pcts = [50, 30, 20]
                else:
                    pcts = [100 / game["num_winners"]] * game["num_winners"]
                share_pct = pcts[idx]
                gross = round(pool * share_pct / 100, 2)
            elif game["allocation_method"] == "FIXED_AMOUNT":
                # Fixed amounts for 4 winners
                amounts = [150000, 120000, 80000, 50000]
                gross = amounts[idx] if idx < len(amounts) else round(pool / game["num_winners"], 2)
                share_pct = round(gross / pool * 100, 2)
            else:
                share_pct = round(100.0 / game["num_winners"], 2)
                gross = round(pool / game["num_winners"], 2)

            alloc = {
                "allocation_id": f"WIN-{game['game_id'].split('-')[1]}-{idx+1:02d}",
                "game_id": game["game_id"],
                "individual_id": winner["individual_id"],
                "gross_winning": gross,
                "allocation_method": game["allocation_method"],
                "share_percentage": share_pct,
                "net_winning": gross,  # before TDS
                "status": "ALLOCATED",
            }
            allocations.append(alloc)

            conn.execute(
                "INSERT INTO winning_allocations "
                "(allocation_id, game_id, individual_id, gross_winning, "
                "allocation_method, share_percentage, net_winning, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (alloc["allocation_id"], alloc["game_id"], alloc["individual_id"],
                 alloc["gross_winning"], alloc["allocation_method"],
                 alloc["share_percentage"], alloc["net_winning"], alloc["status"]),
            )

            # Mark as winner in participants
            conn.execute(
                "UPDATE game_participants SET is_winner = 1 "
                "WHERE game_id = ? AND individual_id = ?",
                (game["game_id"], winner["individual_id"]),
            )

    return allocations


# ─── Transactions ─────────────────────────────────────────────────────
def seed_transactions(conn, individuals, games, participants, allocations):
    """Create transactional ledger entries."""
    txn_count = 0

    # Create individual lookup
    ind_map = {i["individual_id"]: i for i in individuals}

    # Buy-in transactions for every participant
    for part in participants:
        if part["buy_in_amount"] <= 0:
            continue
        ind = ind_map.get(part["individual_id"])
        if not ind:
            continue
        txn_count += 1
        game_info = next((g for g in games if g["game_id"] == part["game_id"]), None)
        conn.execute(
            "INSERT INTO transactions "
            "(transaction_id, pan, game_id, transaction_date, transaction_type, "
            "amount, credit_debit, payment_method, reference_number, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"TXN-BUY-{txn_count:04d}",
                ind["pan"],
                part["game_id"],
                game_info["start_time"] if game_info else datetime.now().isoformat(),
                "BUY_IN",
                part["buy_in_amount"],
                "DEBIT",
                random.choice(["CASH", "CHIPS", "CARD", "UPI"]),
                f"REF-{generate_uuid()}",
                f"Buy-in for {part['game_id']}",
            ),
        )

    # Game entry transactions
    for part in participants:
        ind = ind_map.get(part["individual_id"])
        if not ind:
            continue
        txn_count += 1
        game_info = next((g for g in games if g["game_id"] == part["game_id"]), None)
        conn.execute(
            "INSERT INTO transactions "
            "(transaction_id, pan, game_id, transaction_date, transaction_type, "
            "amount, credit_debit, payment_method, reference_number, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"TXN-ENT-{txn_count:04d}",
                ind["pan"],
                part["game_id"],
                game_info["start_time"] if game_info else datetime.now().isoformat(),
                "GAME_ENTRY",
                0,
                "DEBIT",
                "SYSTEM",
                f"REF-{generate_uuid()}",
                f"Game entry for {part['game_id']}",
            ),
        )

    # Winning transactions
    for alloc in allocations:
        ind = ind_map.get(alloc["individual_id"])
        if not ind:
            continue
        txn_count += 1
        game_info = next((g for g in games if g["game_id"] == alloc["game_id"]), None)
        conn.execute(
            "INSERT INTO transactions "
            "(transaction_id, pan, game_id, transaction_date, transaction_type, "
            "amount, credit_debit, payment_method, reference_number, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"TXN-WIN-{txn_count:04d}",
                ind["pan"],
                alloc["game_id"],
                game_info["end_time"] if game_info else datetime.now().isoformat(),
                "WINNING",
                alloc["gross_winning"],
                "CREDIT",
                "SYSTEM",
                f"REF-{generate_uuid()}",
                f"Winning from {alloc['game_id']} — {alloc['allocation_method']}",
            ),
        )

    # TDS transactions for winners
    for alloc in allocations:
        ind = ind_map.get(alloc["individual_id"])
        if not ind:
            continue
        tds_amount = round(alloc["gross_winning"] * TAX_CONFIG["tds_rate"], 2)
        txn_count += 1
        game_info = next((g for g in games if g["game_id"] == alloc["game_id"]), None)
        conn.execute(
            "INSERT INTO transactions "
            "(transaction_id, pan, game_id, transaction_date, transaction_type, "
            "amount, credit_debit, payment_method, reference_number, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"TXN-TDS-{txn_count:04d}",
                ind["pan"],
                alloc["game_id"],
                game_info["end_time"] if game_info else datetime.now().isoformat(),
                "TDS",
                tds_amount,
                "DEBIT",
                "SYSTEM",
                f"REF-{generate_uuid()}",
                f"TDS deduction on winning from {alloc['game_id']}",
            ),
        )

    # Redemption transactions for some winners
    for alloc in allocations:
        if random.random() > 0.6:
            continue
        ind = ind_map.get(alloc["individual_id"])
        if not ind:
            continue
        tds_amount = round(alloc["gross_winning"] * TAX_CONFIG["tds_rate"], 2)
        net = alloc["gross_winning"] - tds_amount
        txn_count += 1
        conn.execute(
            "INSERT INTO transactions "
            "(transaction_id, pan, game_id, transaction_date, transaction_type, "
            "amount, credit_debit, payment_method, reference_number, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"TXN-RED-{txn_count:04d}",
                ind["pan"],
                alloc["game_id"],
                datetime.now().isoformat(),
                "REDEMPTION",
                net,
                "DEBIT",
                random.choice(["BANK_TRANSFER", "CHEQUE", "CASH"]),
                f"REF-{generate_uuid()}",
                f"Redemption of net winnings from {alloc['game_id']}",
            ),
        )


# ─── Tax Configuration ───────────────────────────────────────────────
def seed_tax_configuration(conn):
    conn.execute(
        "INSERT INTO tax_configurations "
        "(config_id, tax_rate, cess_rate, surcharge_rate, tds_rate, "
        "effective_date, income_category, description, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "TAXCFG-001",
            TAX_CONFIG["tax_rate"],
            TAX_CONFIG["cess_rate"],
            TAX_CONFIG["surcharge_rate"],
            TAX_CONFIG["tds_rate"],
            TAX_CONFIG["effective_date"],
            TAX_CONFIG["income_category"],
            TAX_CONFIG["disclaimer"],
            1,
        ),
    )


# ─── TDS Records ─────────────────────────────────────────────────────
def seed_tds_records(conn, allocations, individuals):
    ind_map = {i["individual_id"]: i for i in individuals}
    tds_records = []

    for idx, alloc in enumerate(allocations):
        ind = ind_map.get(alloc["individual_id"])
        if not ind:
            continue
        tds_amount = round(alloc["gross_winning"] * TAX_CONFIG["tds_rate"], 2)
        rec = {
            "tds_id": f"TDS-{idx+1:04d}",
            "pan": ind["pan"],
            "game_id": alloc["game_id"],
            "gross_amount": alloc["gross_winning"],
            "tds_rate": TAX_CONFIG["tds_rate"],
            "tds_amount": tds_amount,
            "deduction_date": datetime.now().date().isoformat(),
            "status": "DEDUCTED",
            "reference": f"TDSREF-{generate_uuid()}",
        }
        tds_records.append(rec)
        conn.execute(
            "INSERT INTO tds_records "
            "(tds_id, pan, game_id, gross_amount, tds_rate, tds_amount, "
            "deduction_date, status, reference) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (rec["tds_id"], rec["pan"], rec["game_id"], rec["gross_amount"],
             rec["tds_rate"], rec["tds_amount"], rec["deduction_date"],
             rec["status"], rec["reference"]),
        )
    return tds_records


# ─── Tax Calculations ────────────────────────────────────────────────
def seed_tax_calculations(conn, individuals, allocations, tds_records):
    ind_map = {i["individual_id"]: i for i in individuals}
    # Aggregate winnings per individual
    ind_winnings = {}
    for alloc in allocations:
        iid = alloc["individual_id"]
        ind_winnings[iid] = ind_winnings.get(iid, 0) + alloc["gross_winning"]

    # Aggregate TDS per PAN
    pan_tds = {}
    for rec in tds_records:
        pan_tds[rec["pan"]] = pan_tds.get(rec["pan"], 0) + rec["tds_amount"]

    for iid, gross in ind_winnings.items():
        ind = ind_map.get(iid)
        if not ind:
            continue
        tax = round(gross * TAX_CONFIG["tax_rate"], 2)
        cess = round(tax * TAX_CONFIG["cess_rate"], 2)
        surcharge = round(tax * TAX_CONFIG["surcharge_rate"], 2)
        total_tax = round(tax + cess + surcharge, 2)
        tds_ded = pan_tds.get(ind["pan"], 0)
        balance = round(total_tax - tds_ded, 2)

        conn.execute(
            "INSERT INTO tax_calculations "
            "(calculation_id, individual_id, pan, assessment_year, gross_winnings, "
            "taxable_winnings, tax_amount, cess_amount, surcharge_amount, total_tax, "
            "tds_deducted, balance_payable, config_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"TAXCALC-{iid.split('-')[1]}",
                iid, ind["pan"], "2025-26", gross, gross,
                tax, cess, surcharge, total_tax, tds_ded, balance, "TAXCFG-001",
            ),
        )


# ─── ITR Records ─────────────────────────────────────────────────────
def seed_itr_records(conn, individuals, allocations):
    """
    Create ITR records with deliberate scenarios:
    - Correctly reported
    - Under-reported
    - Not reported
    - Over-reported
    """
    ind_map = {i["individual_id"]: i for i in individuals}
    ind_winnings = {}
    for alloc in allocations:
        iid = alloc["individual_id"]
        ind_winnings[iid] = ind_winnings.get(iid, 0) + alloc["gross_winning"]

    itr_records = []

    for idx, ind in enumerate(individuals):
        actual_winnings = ind_winnings.get(ind["individual_id"], 0)
        total_income = round(random.uniform(500000, 2500000), 2)

        # Assign ITR scenarios deliberately
        if idx < 5:
            # Correctly reported
            declared = actual_winnings
            scenario = "CORRECT"
        elif idx < 10:
            # Under-reported
            declared = round(actual_winnings * random.uniform(0.2, 0.7), 2) if actual_winnings > 0 else 0
            scenario = "UNDER-REPORTED"
        elif idx < 14:
            # Not reported at all
            declared = 0
            scenario = "NOT-REPORTED"
        elif idx < 17:
            # Over-reported
            declared = round(actual_winnings * random.uniform(1.2, 1.8), 2) if actual_winnings > 0 else round(random.uniform(10000, 50000), 2)
            scenario = "OVER-REPORTED"
        else:
            # Mixed — some correct, some slight under
            declared = round(actual_winnings * random.uniform(0.85, 1.0), 2) if actual_winnings > 0 else 0
            scenario = "REVIEW"

        tax_paid = round(declared * TAX_CONFIG["tax_rate"] * (1 + TAX_CONFIG["cess_rate"]), 2)

        rec = {
            "itr_id": f"ITR-{idx+1:03d}",
            "individual_id": ind["individual_id"],
            "pan": ind["pan"],
            "assessment_year": "2025-26",
            "filing_date": fake.date_between(start_date="-3m", end_date="today").isoformat(),
            "total_income": total_income + declared,
            "casino_winnings_declared": declared,
            "tax_paid": tax_paid,
            "tds_claimed": round(actual_winnings * TAX_CONFIG["tds_rate"], 2) if actual_winnings > 0 else 0,
            "refund_claimed": 0,
            "itr_form": "ITR-1",
            "verification_status": random.choice(["VERIFIED", "PENDING", "VERIFIED"]),
            "scenario": scenario,
        }
        itr_records.append(rec)

        conn.execute(
            "INSERT INTO itr_records "
            "(itr_id, individual_id, pan, assessment_year, filing_date, total_income, "
            "casino_winnings_declared, tax_paid, tds_claimed, refund_claimed, "
            "itr_form, verification_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (rec["itr_id"], rec["individual_id"], rec["pan"], rec["assessment_year"],
             rec["filing_date"], rec["total_income"], rec["casino_winnings_declared"],
             rec["tax_paid"], rec["tds_claimed"], rec["refund_claimed"],
             rec["itr_form"], rec["verification_status"]),
        )

    return itr_records


# ─── Reconciliations ─────────────────────────────────────────────────
def seed_reconciliations(conn, individuals, allocations, itr_records, tds_records):
    ind_winnings = {}
    for alloc in allocations:
        iid = alloc["individual_id"]
        ind_winnings[iid] = ind_winnings.get(iid, 0) + alloc["gross_winning"]

    pan_tds = {}
    for rec in tds_records:
        pan_tds[rec["pan"]] = pan_tds.get(rec["pan"], 0) + rec["tds_amount"]

    itr_map = {r["individual_id"]: r for r in itr_records}

    for ind in individuals:
        iid = ind["individual_id"]
        casino_win = ind_winnings.get(iid, 0)
        itr = itr_map.get(iid, {})
        declared = itr.get("casino_winnings_declared", 0)
        diff = round(casino_win - declared, 2)
        tds = pan_tds.get(ind["pan"], 0)
        expected_tax = round(casino_win * TAX_CONFIG["tax_rate"] * (1 + TAX_CONFIG["cess_rate"]), 2)
        reported_tax = itr.get("tax_paid", 0)

        # Determine status
        if casino_win == 0 and declared == 0:
            status = "MATCH"
        elif abs(diff) < 1:
            status = "MATCH"
        elif declared == 0 and casino_win > 0:
            status = "NOT-REPORTED"
        elif diff > 0:
            status = "UNDER-REPORTED"
        elif diff < 0:
            status = "OVER-REPORTED"
        else:
            status = "REVIEW"

        remarks = ""
        if status == "MATCH":
            remarks = "Casino winnings match ITR declaration."
        elif status == "UNDER-REPORTED":
            remarks = f"Under-reported by ₹{diff:,.2f}."
        elif status == "NOT-REPORTED":
            remarks = f"Casino winnings of ₹{casino_win:,.2f} not reported in ITR."
        elif status == "OVER-REPORTED":
            remarks = f"Over-reported by ₹{abs(diff):,.2f}."
        else:
            remarks = "Requires manual review."

        conn.execute(
            "INSERT INTO reconciliations "
            "(reconciliation_id, individual_id, pan, assessment_year, "
            "casino_winnings, itr_declared_winnings, difference, tds_deducted, "
            "expected_tax, reported_tax, status, remarks, reconciled_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"RECON-{iid.split('-')[1]}",
                iid, ind["pan"], "2025-26",
                casino_win, declared, diff, tds,
                expected_tax, reported_tax, status, remarks,
                datetime.now().date().isoformat(),
            ),
        )


# ─── Risk Scores ─────────────────────────────────────────────────────
def seed_risk_scores(conn, individuals, allocations, itr_records):
    ind_winnings = {}
    for alloc in allocations:
        iid = alloc["individual_id"]
        ind_winnings[iid] = ind_winnings.get(iid, 0) + alloc["gross_winning"]

    itr_map = {r["individual_id"]: r for r in itr_records}

    for ind in individuals:
        iid = ind["individual_id"]
        casino_win = ind_winnings.get(iid, 0)
        itr = itr_map.get(iid, {})
        declared = itr.get("casino_winnings_declared", 0)

        score = 0
        factors = []

        # Factor 1: Winnings not reported
        if casino_win > 0 and declared == 0:
            score += RISK_RULES["winnings_not_reported"]
            factors.append(f"₹{casino_win:,.0f} casino winnings not declared in ITR")

        # Factor 2: Large under-reporting
        if casino_win > 0 and 0 < declared < casino_win:
            diff = casino_win - declared
            if diff > 50000:
                score += RISK_RULES["large_under_reporting"]
                factors.append(f"₹{diff:,.0f} under-reported (casino: ₹{casino_win:,.0f}, ITR: ₹{declared:,.0f})")

        # Factor 3: Repeated mismatches (simulated)
        if itr.get("scenario") in ("UNDER-REPORTED", "NOT-REPORTED"):
            if random.random() > 0.5:
                score += RISK_RULES["repeated_mismatches"]
                factors.append("Multiple assessment years with mismatches (simulated)")

        # Factor 4: Large cash activity
        if casino_win > 200000:
            score += RISK_RULES["large_cash_activity"]
            factors.append(f"High-value casino activity: ₹{casino_win:,.0f}")

        # Factor 5: Frequent high-value transactions
        if casino_win > 300000:
            score += RISK_RULES["frequent_high_value_txns"]
            factors.append("Frequent high-value transactions detected")

        # Cap at 100
        score = min(score, 100)

        # Determine risk level
        risk_level = "LOW"
        for level, (lo, hi) in RISK_THRESHOLDS.items():
            if lo <= score <= hi:
                risk_level = level
                break

        if not factors:
            factors.append("No significant risk factors identified")

        conn.execute(
            "INSERT INTO risk_scores "
            "(risk_id, individual_id, pan, score, risk_level, factors, assessment_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                f"RISK-{iid.split('-')[1]}",
                iid, ind["pan"], score, risk_level,
                json.dumps(factors),
                datetime.now().date().isoformat(),
            ),
        )

        # Update individual's risk score
        conn.execute(
            "UPDATE individuals SET risk_score = ? WHERE individual_id = ?",
            (score, iid),
        )


# ─── Audit Logs ───────────────────────────────────────────────────────
def seed_audit_logs(conn):
    actions = [
        ("SYSTEM", "DATABASE_INIT", "database", "DB-001", None, "initialized", "Database schema created"),
        ("SYSTEM", "SEED_DATA", "individuals", "ALL", None, "20 records", "Seeded 20 synthetic individuals"),
        ("SYSTEM", "SEED_DATA", "games", "ALL", None, "20 records", "Seeded 20 synthetic games"),
        ("SYSTEM", "SEED_DATA", "transactions", "ALL", None, "100+ records", "Seeded transaction ledger"),
        ("ADMIN", "RECONCILIATION_RUN", "reconciliations", "ALL", None, "completed", "Full reconciliation executed"),
        ("ADMIN", "RISK_ASSESSMENT", "risk_scores", "ALL", None, "scored", "Risk assessment completed"),
    ]
    for idx, (user, action, entity, eid, old, new, desc) in enumerate(actions):
        conn.execute(
            "INSERT INTO audit_logs "
            "(audit_id, user_id, action, entity, entity_id, old_value, new_value, "
            "ip_address, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f"AUDIT-{idx+1:04d}", user, action, entity, eid, old, new, "DEMO", desc),
        )


# ─── CSV Export ───────────────────────────────────────────────────────
def export_csvs(conn):
    """Export key tables to CSV for reference."""
    import pandas as pd
    from config.settings import DATA_DIR

    tables = {
        "users_20.csv": "SELECT * FROM individuals",
        "games_20.csv": "SELECT * FROM games",
        "participants.csv": "SELECT * FROM game_participants",
        "itr_records.csv": "SELECT * FROM itr_records",
        "test_scenarios.csv": """
            SELECT g.game_id, g.game_type, g.prize_pool,
                   g.num_winners, g.allocation_method, g.description,
                   g.status
            FROM games g
            ORDER BY g.game_id
        """,
    }

    for filename, query in tables.items():
        df = pd.read_sql_query(query, conn)
        df.to_csv(DATA_DIR / filename, index=False)


if __name__ == "__main__":
    seed_all()
    print("✅ Database seeded successfully with synthetic data.")
