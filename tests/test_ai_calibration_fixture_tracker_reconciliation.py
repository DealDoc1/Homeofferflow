import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_ai_calibration_fixture_pack_reconciliation.sql").read_text(encoding="utf-8")


class AiCalibrationFixtureTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_stays_partial_until_human_review(self):
        self.assertIn("where slug = 'ai-offer-competitiveness'", SQL)
        self.assertIn("status = 'in_progress'", SQL)
        self.assertIn("qa_status = 'partial'", SQL)
        self.assertIn("AI-CAL-01", SQL)
        self.assertIn("AI-CAL-05", SQL)
        self.assertIn("independent Texas broker or agent review", SQL)
        self.assertNotIn("status = 'production'", SQL)


if __name__ == "__main__":
    unittest.main()
