import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "homeofferflow_mobile_app_roadmap.sql").read_text(encoding="utf-8")
RECONCILIATION = (ROOT / "supabase" / "migrations" / "20260814170000_reconcile_mobile_pwa_tracker.sql").read_text(encoding="utf-8")


class MobileAppRoadmapTests(unittest.TestCase):
    def test_mobile_app_is_a_deferred_cross_platform_initiative(self):
        self.assertIn("'mobile-app'", SQL)
        self.assertIn("'HomeOfferFlow mobile app'", SQL)
        self.assertIn("'deferred'", SQL)
        self.assertIn("'backlog'", SQL)
        self.assertIn('"iOS"', SQL)
        self.assertIn('"Android"', SQL)

    def test_mobile_roadmap_preserves_web_and_offer_data_security_gates(self):
        self.assertIn("responsive web app remains the supported mobile experience", SQL)
        self.assertIn("Reuse the existing Supabase authorization model", SQL)
        self.assertIn("do not ship an app that broadens buyer or offer-data access", SQL)

    def test_production_pwa_is_distinguished_from_a_future_native_app(self):
        self.assertIn("status = 'in_progress'", RECONCILIATION)
        self.assertIn("environment = 'production'", RECONCILIATION)
        self.assertIn("qa_status = 'partial'", RECONCILIATION)
        self.assertIn("'pwa_status', 'production'", RECONCILIATION)
        self.assertIn("'native_status', 'not_started'", RECONCILIATION)
        self.assertIn("no_api_documents_or_authenticated_data", RECONCILIATION)


if __name__ == "__main__":
    unittest.main()
