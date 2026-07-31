import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_ai_calibration_tracker_reconciliation.sql").read_text(encoding="utf-8")


class AiCalibrationTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_separates_outputs_from_human_evidence(self):
        self.assertIn("generated review-output volume", SQL)
        self.assertIn("anonymized human calibration notes", SQL)
        self.assertIn("five-scenario expert-review threshold", SQL)

    def test_tracker_keeps_broker_agent_review_as_next_gate(self):
        self.assertIn("experienced Texas broker or agent", SQL)
        self.assertIn("misleading, unsafe, or missing output", SQL)
        self.assertIn("ai-offer-competitiveness", SQL)


if __name__ == "__main__":
    unittest.main()
