from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_tracker_reconciliation_2026_08_08.sql").read_text(encoding="utf-8")


class TrackerReconciliation20260808Tests(unittest.TestCase):
    def test_reconciliation_records_verified_production_commit(self):
        self.assertIn("3abba8d [deploy-production] Bundle verified HomeOfferFlow release", SQL)

    def test_reconciliation_is_metadata_only_and_keeps_form_gates(self):
        self.assertIn("Metadata only", SQL)
        self.assertIn("completed visual QA", SQL)
        self.assertIn("priority in (10, 14, 15)", SQL)
        self.assertIn("priority in (27, 28, 29)", SQL)
        self.assertNotIn("create table", SQL.lower())


if __name__ == "__main__":
    unittest.main()
