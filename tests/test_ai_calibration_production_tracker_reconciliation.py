from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_ai_calibration_production_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class AiCalibrationProductionTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_records_production_release_without_overclaiming_calibration(self):
        self.assertIn("where slug = 'ai-offer-competitiveness'", SQL)
        self.assertIn("reviewer-role threshold hardening (production", SQL)
        self.assertIn("Scoring and wording remain unchanged", SQL)
        self.assertIn("five anonymized broker/agent calibration scenarios", SQL)


if __name__ == "__main__":
    unittest.main()
