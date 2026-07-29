import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "homeofferflow_ai_benchmark_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class AiBenchmarkTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_records_the_released_benchmark_and_response_hardening(self):
        self.assertIn("AI offer-review benchmark and live-response safety hardening", MIGRATION)
        self.assertIn("ai-offer-competitiveness", MIGRATION)

    def test_tracker_retains_human_calibration_gate(self):
        self.assertIn("experienced Texas broker or agent", MIGRATION)
        self.assertIn("anonymized real transaction scenarios", MIGRATION)
        self.assertIn("property valuation", MIGRATION)


if __name__ == "__main__":
    unittest.main()
