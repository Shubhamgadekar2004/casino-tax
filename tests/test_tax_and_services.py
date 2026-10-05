"""
Unit and System Integration Tests for Casino Tax & Accounting Demo System.
"""
import unittest
import os

from config.settings import DB_PATH
from database.database import init_database, execute_query, is_database_seeded
from database.seed_data import seed_all
from models.individual import get_individual_by_id, get_all_individuals, get_individual_by_pan, search_individuals
from models.game import get_all_games, get_game_by_id
from services.winnings_service import allocate_winnings
from services.tax_service import calculate_tax, calculate_game_tax
from services.reconciliation_service import reconcile_individual, get_reconciliation_summary
from services.risk_service import calculate_risk_score
from services.audit_service import log_action, get_recent_logs
from services.report_service import generate_pdf_tax_certificate, generate_excel_export


class TestCasinoTaxSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database and seed data once before running tests."""
        init_database()
        if not is_database_seeded():
            seed_all()

    def test_01_database_seeded(self):
        """Test database initialization and seeding."""
        self.assertTrue(is_database_seeded())
        inds = get_all_individuals()
        self.assertGreater(len(inds), 0)

    def test_02_individual_retrieval(self):
        """Test retrieving individuals by ID, PAN, and search."""
        inds = get_all_individuals()
        first_ind = inds[0]
        ind_id = first_ind["individual_id"]

        ind = get_individual_by_id(ind_id)
        self.assertIsNotNone(ind)
        self.assertEqual(ind["individual_id"], ind_id)

        ind_pan = get_individual_by_pan(ind["pan"])
        self.assertIsNotNone(ind_pan)
        self.assertEqual(ind_pan["pan"], ind["pan"])

    def test_03_winnings_allocation(self):
        """Test equal split, proportional, and winner-takes-all winnings allocation."""
        participants = [
            {"participant_id": "P1", "individual_id": "IND-TEST1", "name": "P1", "buy_in": 10000, "rank": 1},
            {"participant_id": "P2", "individual_id": "IND-TEST2", "name": "P2", "buy_in": 30000, "rank": 2},
        ]

        # Equal Split
        alloc_equal = allocate_winnings("G-TEST", 100000, participants, rule="EQUAL_SPLIT")
        self.assertEqual(len(alloc_equal), 2)
        self.assertEqual(alloc_equal[0]["allocated_amount"], 50000)
        self.assertEqual(alloc_equal[1]["allocated_amount"], 50000)

        # Proportional Buyin
        alloc_prop = allocate_winnings("G-TEST", 100000, participants, rule="PROPORTIONAL_BUYIN")
        self.assertEqual(alloc_prop[0]["allocated_amount"], 25000)
        self.assertEqual(alloc_prop[1]["allocated_amount"], 75000)

        # Winner Takes All
        alloc_wta = allocate_winnings("G-TEST", 100000, participants, rule="WINNER_TAKES_ALL")
        self.assertEqual(alloc_wta[0]["allocated_amount"], 100000)
        self.assertEqual(alloc_wta[1]["allocated_amount"], 0)

    def test_04_tax_calculation(self):
        """Test Section 115BB flat 30% tax calculation and 194B TDS."""
        tax = calculate_game_tax(gross_winnings=100000, buy_in=20000)
        self.assertEqual(tax["gross_winnings"], 100000)
        self.assertEqual(tax["tax_rate_percent"], 30.0)
        self.assertEqual(tax["tax_amount"], 30000)
        self.assertEqual(tax["tax_calculated"], 31200)
        self.assertEqual(tax["tds_deducted"], 30000)
        self.assertEqual(tax["net_payout"], 70000)

    def test_05_reconciliation_logic(self):
        """Test ITR Reconciliation logic."""
        inds = get_all_individuals()
        if inds:
            reco = reconcile_individual(inds[0]["individual_id"], declared_winnings=500000)
            self.assertIsNotNone(reco)
            self.assertIn("status", reco)

    def test_06_risk_engine(self):
        """Test automated risk scoring engine."""
        inds = get_all_individuals()
        if inds:
            risk = calculate_risk_score(inds[0]["individual_id"])
            self.assertIn("risk_score", risk)
            self.assertIn("risk_tier", risk)
            self.assertGreaterEqual(risk["risk_score"], 0)

    def test_07_audit_trail(self):
        """Test immutable audit log creation."""
        log_action(user="UNIT_TEST", action="TEST_ACTION", entity="TEST", description="Unit test log entry")
        logs = get_recent_logs(limit=10)
        test_logs = [l for l in logs if l["user_id"] == "UNIT_TEST"]
        self.assertGreater(len(test_logs), 0)

    def test_08_pdf_report_generation(self):
        """Test PDF Tax Certificate generation."""
        inds = get_all_individuals()
        if inds:
            pdf_bytes = generate_pdf_tax_certificate(inds[0]["individual_id"])
            self.assertIsInstance(pdf_bytes, bytes)
            self.assertGreater(len(pdf_bytes), 100)

    def test_09_excel_report_generation(self):
        """Test Excel Multi-tab export generation."""
        excel_bytes = generate_excel_export()
        self.assertIsInstance(excel_bytes, bytes)
        self.assertGreater(len(excel_bytes), 500)


if __name__ == "__main__":
    unittest.main()
