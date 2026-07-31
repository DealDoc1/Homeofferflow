from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL = (
    ROOT
    / "supabase"
    / "homeofferflow_seller_listing_catalog_tracker_reconciliation.sql"
).read_text(encoding="utf-8")


class SellerListingCatalogTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_records_catalog_without_enabling_forms(self):
        self.assertIn("where slug = 'seller-workflow'", SQL)
        self.assertIn("intake catalog and golden scenarios", SQL)
        self.assertIn("remain source-gated", SQL)
        self.assertIn("rendered completed-PDF QA", SQL)


if __name__ == "__main__":
    unittest.main()
