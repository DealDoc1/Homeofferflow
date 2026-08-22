from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_reconcile_live_txr_1914_draft.sql").read_text(encoding="utf-8")


class LiveTxr1914RoadmapReconciliationTests(unittest.TestCase):
    def test_reconciles_private_review_without_claiming_a_signature_release(self):
        self.assertIn("where slug = 'seller-financing'", SQL)
        self.assertIn("status = 'in_progress'", SQL)
        self.assertIn("no loan-document, signature-send", SQL)
        self.assertIn("completed-signature visual QA", SQL)


if __name__ == "__main__":
    unittest.main()
