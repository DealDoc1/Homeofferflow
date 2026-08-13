import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
SPEC = importlib.util.spec_from_file_location("fsbo_onboarding", ROOT / "api" / "fsbo-lead.py")
fsbo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fsbo)


class PartnerSelfServiceOnboardingTests(unittest.TestCase):
    def test_migration_hashes_and_expires_single_use_tokens(self):
        sql = (ROOT / "supabase/migrations/20260810123000_partner_self_service_onboarding.sql").read_text()
        self.assertIn("onboarding_token_hash", sql)
        self.assertIn("onboarding_token_expires_at", sql)
        self.assertIn("raw tokens are never stored", sql)

    def test_only_secure_urls_are_accepted_for_public_creative(self):
        self.assertEqual(fsbo._secure_url("https://example.com/logo.png", "Logo URL"), "https://example.com/logo.png")
        with self.assertRaisesRegex(ValueError, "secure https"):
            fsbo._secure_url("http://example.com/logo.png", "Logo URL")

    def test_public_payload_omits_partner_contact_data(self):
        payload = fsbo._public_partner_onboarding({"company_name": "North Texas Title", "contact_email": "private@example.com", "market_area": "DFW"})
        self.assertEqual(payload["company_name"], "North Texas Title")
        self.assertNotIn("contact_email", payload)

    def test_completed_setup_clears_the_token_and_does_not_activate_placement(self):
        lead = {"id": "lead-1", "company_name": "North Texas Title"}
        response = type("Response", (), {"status_code": 200, "text": '[{}]', "json": lambda self: [{"company_name": "North Texas Title"}]})()
        class Client:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def patch(self, *args, **kwargs): self.payload = kwargs["json"]; return response
        client = Client()
        with patch.object(fsbo, "_get_partner_onboarding", return_value=lead), patch.object(fsbo.httpx, "Client", return_value=client):
            fsbo._complete_partner_onboarding("A" * 32, {"market_area": "DFW", "website_url": "https://example.com"})
        self.assertIsNone(client.payload["onboarding_token_hash"])
        self.assertEqual(client.payload["onboarding_status"], "complete")
        self.assertNotIn("is_active", client.payload)

    def test_public_and_admin_surfaces_keep_activation_separate(self):
        html = (ROOT / "index.html").read_text()
        admin = (ROOT / "api/admin-dashboard.py").read_text()
        self.assertIn("partner_onboarding_submit", html)
        self.assertIn("create_partner_onboarding_link", admin)
        self.assertIn("written placement agreement", html)

    def test_browser_removes_the_bearer_token_from_the_visible_url_after_loading(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn("const partnerOnboardingTokenKey = 'hof_partner_onboarding_token';", html)
        self.assertIn("function retainPartnerOnboardingToken(token)", html)
        self.assertIn("cleanUrl.searchParams.delete('partner_onboarding');", html)
        self.assertIn("window.history.replaceState({}, document.title, cleanUrl.pathname + cleanUrl.search + cleanUrl.hash);", html)
        self.assertIn("clearPartnerOnboardingToken();", html)

    def test_partner_setup_explains_and_validates_the_only_required_setup_field(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn('id="partnerSetupMarket" placeholder="Market area" required aria-required="true"', html)
        self.assertIn("Your primary market area is the only setup field required.", html)
        self.assertIn("Enter the primary market area before saving setup details.", html)
        self.assertIn("const market = value('partnerSetupMarket');", html)
        self.assertIn("market_area:market", html)
        self.assertIn("Website (https, optional)", html)

    def test_admin_exposes_paid_partner_setup_completion_funnel(self):
        admin = (ROOT / "api/admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        self.assertIn("partnerOnboardingInProgressCount", admin)
        self.assertIn("partnerOnboardingCompletedCount", admin)
        self.assertIn("partnerOnboardingCompletionRate", html)

    def test_admin_exposes_aggregate_secure_setup_email_delivery_metric(self):
        admin = (ROOT / "api/admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        self.assertIn('"partnerOnboardingEmailSentCount": partner_onboarding_email_sent_count', admin)
        self.assertIn('item.get("event_type") == "partner_onboarding_email_sent"', admin)
        self.assertIn("manual setup emails sent", html)

    def test_admin_exposes_automatic_checkout_setup_invitation_metric(self):
        admin = (ROOT / "api" / "admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        self.assertIn('"partnerOnboardingSetupIssuedCount": partner_onboarding_setup_issued_count', admin)
        self.assertIn('item.get("event_type") == "partner_onboarding_setup_issued"', admin)
        self.assertIn("checkout setup invitations issued", html)

    def test_admin_tracks_manual_setup_link_creation_and_preserves_a_link_when_copying_fails(self):
        admin = (ROOT / "api/admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        self.assertIn('"partnerOnboardingLinkCreatedCount": partner_onboarding_link_created_count', admin)
        self.assertIn('item.get("event_type") == "partner_onboarding_link_created"', admin)
        self.assertIn("partner_onboarding_link_created", html)
        self.assertIn("window.prompt('Copy this secure partner setup link", html)
        self.assertIn("secure setup links created", html)

    def test_admin_can_send_setup_link_only_from_an_explicit_paid_partner_action(self):
        admin = (ROOT / "api/admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        self.assertIn("email_partner_onboarding_link", admin)
        self.assertIn("_email_partner_onboarding_link", admin)
        self.assertIn("Email setup link", html)
        self.assertIn("emailPartnerOnboardingLink", html)
        self.assertIn("does not activate advertising", admin)


if __name__ == "__main__":
    unittest.main()
