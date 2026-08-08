import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_production_activation_tracker_reconciliation_2026_08_08.sql"
).read_text(encoding="utf-8")


class ProductionActivationTrackerReconciliationTests(unittest.TestCase):
    def test_reconciles_live_runtime_without_unlocking_gated_forms(self):
        self.assertIn("trec-20-19-controlled-launch", SQL)
        self.assertIn("0c66ef3", SQL)
        self.assertIn("homeofferflow-58avpsqgn-dealdoc1s-projects.vercel.app", SQL)
        self.assertIn("completed signed-PDF visual QA", SQL)
        self.assertIn("remain fail-closed", SQL)
        self.assertIn("where release_key = 'trec-20-19-controlled-launch'", SQL)


if __name__ == "__main__":
    unittest.main()
