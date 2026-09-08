from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_reconcile_live_txr_1919_draft.sql").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "migrations" / "20260907120000_reconcile_live_txr_1919_draft.sql").read_text(encoding="utf-8")


class LiveTxr1919RoadmapReconciliationTests(unittest.TestCase):
    def test_reconciles_private_review_without_claiming_a_signature_release(self):
        for source in (SQL, MIGRATION):
            self.assertIn("where slug = 'loan-assumption'", source)
            self.assertIn("status = 'in_progress'", source)
            self.assertIn("qa_status = 'partial'", source)
            self.assertIn("no loan-document, lender-contact, signature-send", source)
            self.assertIn("completed-signature visual QA", source)


if __name__ == "__main__":
    unittest.main()
