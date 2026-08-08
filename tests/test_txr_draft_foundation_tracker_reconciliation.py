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
        self.assertIn("current_release = '259c6ee TXR-1507 unsigned one/two-client render recheck (2026-08-08)'", MIGRATION)
        self.assertIn("authenticated point-of-use QA", MIGRATION)
        self.assertIn("completed-signature visual QA", MIGRATION)
        self.assertIn("cannot send or promote forms by themselves", MIGRATION)


if __name__ == "__main__":
    unittest.main()
