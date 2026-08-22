import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_brokerage_branding_tracker_reconciliation.sql").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")


class BrokerageBrandingTrackerReconciliationTests(unittest.TestCase):
    def test_tracker_records_implemented_upload_but_keeps_qa_gate(self):
        self.assertIn("Broker-admin-only logo upload", SQL)
        self.assertIn("PDF visual branding", SQL)
        self.assertIn("signing-message propagation", SQL)
        self.assertIn("authenticated brokerage-admin QA", SQL)
        self.assertIn("where slug = 'brokerage-branding'", SQL)

    def test_broker_admin_branding_upload_is_present_and_validated(self):
        self.assertIn("brokerageLogoFile", INDEX)
        self.assertIn("image/png", INDEX)
        self.assertIn("2 * 1024 * 1024", INDEX)
        self.assertIn("brokerage-branding", INDEX)
        self.assertIn("BROKERAGE_BRANDING_BUCKET", ADMIN)
        self.assertIn("Only active brokerage admins", INDEX)

    def test_legacy_branding_foundation_does_not_offer_a_rejected_external_logo_url(self):
        foundation_start = INDEX.index("function renderBrokerageFoundationPanel()")
        foundation_end = INDEX.index("function renderSellerFoundationPanel()", foundation_start)
        foundation = INDEX[foundation_start:foundation_end]
        self.assertNotIn('id="brandLogoUrl"', foundation)
        self.assertNotIn("logo_url: getVal('brandLogoUrl')", foundation)
        self.assertIn("External logo URLs are intentionally not accepted.", foundation)
        self.assertIn("secure direct-upload control in Brokerage Administration below", foundation)


if __name__ == "__main__":
    unittest.main()
