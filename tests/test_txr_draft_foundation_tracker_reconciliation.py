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
        self.assertIn("else 'Private draft foundation'", MIGRATION)
        self.assertIn("then 'Private draft foundation + renderer QA'", MIGRATION)
        self.assertIn("then 'partial'", MIGRATION)
        self.assertIn("completed SignWell packet QA is still pending", MIGRATION)
        self.assertIn("cannot expose, generate, send, or sign", MIGRATION)


if __name__ == "__main__":
    unittest.main()
