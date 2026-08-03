from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_ai_calibration_reviewer_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class AiCalibrationReviewerTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_preserves_structured_review_evidence_gate(self):
        self.assertIn("where slug = 'ai-offer-competitiveness'", SQL)
        self.assertIn("d9eb70b structured AI calibration review evidence", SQL)
        self.assertIn("Human calibration review is still required", SQL)
        self.assertIn("five anonymized broker/experienced-agent calibration scenarios", SQL)


if __name__ == "__main__":
    unittest.main()
