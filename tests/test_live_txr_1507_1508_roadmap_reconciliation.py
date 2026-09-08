from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_reconcile_live_txr_1507_1508_drafts.sql").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "migrations" / "20260907130000_reconcile_live_txr_1507_1508_drafts.sql").read_text(encoding="utf-8")


class LiveTxr1507And1508RoadmapReconciliationTests(unittest.TestCase):
    def test_reconciles_shared_private_reviews_without_claiming_signature_release(self):
        for source in (SQL, MIGRATION):
            self.assertIn("'txr-1507-short-buyer-tenant-representation'", source)
            self.assertIn("'txr-1508-unrepresented-showing'", source)
            self.assertIn("status = 'in_progress'", source)
            self.assertIn("environment = 'production'", source)
            self.assertIn("qa_status = 'partial'", source)
            self.assertIn("available to every signed-in agent", source)
            self.assertIn("no signature-send or completed-signature route", source)
            self.assertIn("source-specific signer map and completed-signature visual QA", source)


if __name__ == "__main__":
    unittest.main()
