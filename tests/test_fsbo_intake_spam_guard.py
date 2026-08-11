from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")


class FsboIntakeSpamGuardTests(unittest.TestCase):
    def test_hidden_seller_field_is_accepted_without_creating_a_follow_up_record(self):
        self.assertIn("if _text(data.get('fsbo_website_confirm'), 250):", API)
        self.assertIn("polluting the public FSBO follow-up queue", API)
        guard_start = API.index("if _text(data.get('fsbo_website_confirm'), 250):")
        insert_start = API.index("url = f'{SUPABASE_URL}/rest/v1/hof_seller_leads'")
        self.assertLess(guard_start, insert_start)

    def test_server_deduplicates_recent_same_package_seller_requests(self):
        self.assertIn("def _recent_matching_fsbo_lead", API)
        self.assertIn('"seller_email": f"ilike.{email}"', API)
        self.assertIn('"service_level": f"eq.{service_level}"', API)
        self.assertIn("timedelta(hours=24)", API)
        self.assertIn('"duplicate": True', API)

    def test_server_canonicalizes_the_supported_seller_package_catalog(self):
        self.assertIn("FSBO_PACKAGE_CATALOG", API)
        self.assertIn("Choose a supported seller package.", API)
        self.assertIn("package_name, package_price = FSBO_PACKAGE_CATALOG[service_level]", API)

    def test_public_intake_cannot_set_its_own_crm_status(self):
        self.assertIn("Public seller intake is never allowed to choose its CRM", API)
        self.assertIn("'status': 'new'", API)
        self.assertNotIn("'status': _text(data.get('status')", API)


if __name__ == "__main__":
    unittest.main()
