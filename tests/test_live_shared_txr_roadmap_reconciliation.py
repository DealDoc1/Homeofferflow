from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_reconcile_live_shared_txr_drafts.sql").read_text(encoding="utf-8")


class LiveSharedTxrRoadmapReconciliationTests(unittest.TestCase):
    def test_reconciles_verified_private_drafts_without_claiming_signature_release(self):
        self.assertIn("status = 'in_progress'", SQL)
        self.assertIn("'txr-1501-long-buyer-tenant-representation'", SQL)
        self.assertIn("'txr-1506-general-information-notice'", SQL)
        self.assertIn("'mineral-reservation-addendum'", SQL)
        self.assertIn("no signature-send route", SQL)
        self.assertIn("Completed signature PDF visual QA", SQL)


if __name__ == "__main__":
    unittest.main()
