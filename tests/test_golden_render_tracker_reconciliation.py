import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "homeofferflow_golden_render_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class GoldenRenderTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_records_approved_baseline_without_replacing_human_pdf_qa(self):
        self.assertIn("automated-visual-regression", MIGRATION)
        self.assertIn("11-scenario golden rendered-PDF baseline verified", MIGRATION)
        self.assertIn("does not replace human review", MIGRATION)
        self.assertIn("scripts/check_golden_packet_rendering.py", MIGRATION)


if __name__ == "__main__":
    unittest.main()
