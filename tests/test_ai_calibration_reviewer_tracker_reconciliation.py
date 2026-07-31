from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_ai_calibration_reviewer_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class AiCalibrationReviewerTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_marks_reviewer_role_safeguard_as_staged(self):
        self.assertIn("where slug = 'ai-offer-competitiveness'", SQL)
        self.assertIn("reviewer-role threshold hardening (staged", SQL)
        self.assertIn("has not been bundled into the next intentional Vercel production release", SQL)
        self.assertIn("five anonymized broker/agent calibration scenarios", SQL)


if __name__ == "__main__":
    unittest.main()
