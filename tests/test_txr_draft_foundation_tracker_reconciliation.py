from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase" / "homeofferflow_txr_draft_foundation_tracker_reconciliation.sql"
).read_text()


class TxrDraftFoundationTrackerReconciliationTests(unittest.TestCase):
    def test_all_private_txr_drafts_stay_source_gated(self):
        for slug in (
            "txr-1507-short-buyer-tenant-representation",
            "txr-1501-long-buyer-tenant-representation",
            "txr-1508-unrepresented-showing",
            "txr-1506-general-information-notice",
        ):
            self.assertIn(slug, MIGRATION)
        self.assertIn("status = 'blocked'", MIGRATION)
        self.assertIn("environment = 'source_gate'", MIGRATION)
        self.assertIn("current_release = 'Unsigned local source/render QA verified 2026-08-03'", MIGRATION)
        self.assertIn("cannot expose, generate, send, or sign", MIGRATION)


if __name__ == "__main__":
    unittest.main()
