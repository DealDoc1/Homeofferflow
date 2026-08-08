from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_ai_calibration_bundle_tracker_reconciliation_2026_08_08.sql").read_text(
    encoding="utf-8"
)


class AICalibrationBundleTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_keeps_partial_status_and_five_review_gate(self):
        self.assertIn("where slug = 'ai-offer-competitiveness'", SQL)
        self.assertIn("status = 'in_progress'", SQL)
        self.assertIn("qa_status = 'partial'", SQL)
        self.assertIn("e381f59 AI calibration reviewer bundle", SQL)
        self.assertIn("AI-CAL-01 through AI-CAL-05", SQL)
        self.assertIn("not yet been recorded", SQL)


if __name__ == "__main__":
    unittest.main()
