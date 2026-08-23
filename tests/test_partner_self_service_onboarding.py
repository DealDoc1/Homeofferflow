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
        sql = (ROOT / "supabase/migrations/20260810175019_partner_self_service_onboarding.sql").read_text()
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
        with patch.object(fsbo, "_get_partner_onboarding", return_value=lead), \
             patch.object(fsbo, "_record_partner_onboarding_event") as record, \
             patch.object(fsbo.httpx, "Client", return_value=client):
            fsbo._complete_partner_onboarding("A" * 32, {"market_area": "DFW", "website_url": "https://example.com"})
        self.assertIsNone(client.payload["onboarding_token_hash"])
        self.assertEqual(client.payload["onboarding_status"], "complete")
        self.assertNotIn("is_active", client.payload)
        record.assert_called_once_with("partner_onboarding_completed")

    def test_completed_checkout_recovery_rotates_a_setup_token_only_for_the_matching_paid_row(self):
        lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"
        response = type("Response", (), {"status_code": 200, "text": '[{}]', "json": lambda self: [{"id": lead_id}]})()
        class Client:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def patch(self, *args, **kwargs): self.url, self.payload = args[0], kwargs["json"]; return response
        client = Client()
        session = {"status": "complete", "metadata": {"partner_lead_id": lead_id}}
        with patch.object(fsbo, "_retrieve_partner_checkout_session", return_value=session), \
             patch.object(fsbo, "_get_paid_partner_for_checkout_recovery", return_value={"id": lead_id, "status": "approved", "onboarding_status": "ready"}), \
             patch.object(fsbo, "_record_partner_checkout_event") as record, \
             patch.object(fsbo.httpx, "Client", return_value=client):
            result = fsbo._recover_partner_onboarding_from_checkout("cs_test_12345678")
        self.assertEqual(result["state"], "ready")
        self.assertTrue(result["onboarding_token"])
        self.assertNotEqual(client.payload["onboarding_token_hash"], result["onboarding_token"])
        self.assertIn("payment_status=eq.paid", client.url)
        self.assertIn("stripe_checkout_session_id=eq.cs_test_12345678", client.url)
        record.assert_called_once_with(
            "partner_checkout_setup_recovered", "ready",
            "Partner resumed secure setup from a completed checkout.",
            {"surface": "checkout_success_return"},
        )

    def test_checkout_recovery_waits_for_the_signed_webhook_to_mark_payment(self):
        lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"
        session = {"status": "complete", "metadata": {"partner_lead_id": lead_id}}
        with patch.object(fsbo, "_retrieve_partner_checkout_session", return_value=session), \
             patch.object(fsbo, "_get_paid_partner_for_checkout_recovery", return_value=None):
            result = fsbo._recover_partner_onboarding_from_checkout("cs_test_12345678")
        self.assertEqual(result, {"state": "processing"})

    def test_checkout_recovery_rejects_invalid_session_ids_before_any_stripe_request(self):
        with self.assertRaisesRegex(ValueError, "valid checkout confirmation"):
            fsbo._retrieve_partner_checkout_session("https://stripe.example/anything")

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
        self.assertIn("Setup details saved — you are all set for now.", html)
        self.assertIn("We will only publish a placement after that review is complete.", html)
        self.assertIn("window.history.replaceState({}, document.title, cleanUrl.pathname + cleanUrl.search + cleanUrl.hash);", html)
        self.assertIn("clearPartnerOnboardingToken();", html)

    def test_checkout_success_recovers_setup_without_retaining_the_stripe_session_id(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn("async function recoverPartnerCheckoutSetup(sessionId, attempt = 0)", html)
        self.assertIn("request_type:'founding_partner_checkout_setup'", html)
        self.assertIn("['partner_checkout', 'session_id'].forEach", html)
        self.assertIn("retainPartnerOnboardingToken(result.onboarding_token);", html)
        self.assertIn("attempt < 4", html)
        self.assertIn("window.setTimeout(() => recoverPartnerCheckoutSetup(sessionId, attempt + 1), 2500);", html)

    def test_partner_setup_explains_and_validates_the_only_required_setup_field(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn('id="partnerSetupMarket" placeholder="Market area" required aria-required="true"', html)
        self.assertIn("Your primary market area is the only setup field required.", html)
        self.assertIn("Enter the primary market area before saving setup details.", html)
        self.assertIn("const market = value('partnerSetupMarket');", html)
        self.assertIn("market_area:market", html)
        self.assertIn("Website (https, optional)", html)

    def test_partner_setup_save_announces_progress_and_prevents_duplicate_submissions(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn('id="partnerOnboardingStatus" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', html)
        self.assertIn('const saveButton = document.querySelector(\'#partnerOnboardingFields button[onclick="submitPartnerOnboarding()"]\');', html)
        self.assertIn("saveButton.disabled = true", html)
        self.assertIn("saveButton.setAttribute('aria-busy', 'true')", html)
        self.assertIn("saveButton.textContent = 'Saving setup…'", html)
        self.assertIn("status.textContent = 'Saving setup details…'", html)
        self.assertIn("saveButton.disabled = false", html)
        self.assertIn("saveButton.textContent = 'Save setup details'", html)

    def test_admin_exposes_paid_partner_setup_completion_funnel(self):
        admin = (ROOT / "api/admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        self.assertIn("partnerOnboardingInProgressCount", admin)
        self.assertIn("partnerOnboardingCompletedCount", admin)
        self.assertIn("partnerOnboardingCompletionRate", html)

    def test_onboarding_progress_events_are_aggregate_only_and_visible_to_admin(self):
        admin = (ROOT / "api/admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        source = (ROOT / "api/fsbo-lead.py").read_text()
        self.assertIn('"partner_onboarding_opened": "opened"', source)
        self.assertIn('"partner_onboarding_completed": "completed"', source)
        self.assertIn('"surface": "partner_onboarding"', source)
        self.assertIn('"partnerOnboardingOpenedEventCount": partner_onboarding_opened_event_count', admin)
        self.assertIn('"partnerOnboardingCompletedEventCount": partner_onboarding_completed_event_count', admin)
        self.assertIn("Setup engagement:", html)

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

    def test_admin_separates_self_service_checkout_return_recovery_from_manual_setup_outreach(self):
        admin = (ROOT / "api" / "admin-dashboard.py").read_text()
        html = (ROOT / "index.html").read_text()
        self.assertIn('item.get("event_type") == "partner_checkout_setup_recovered"', admin)
        self.assertIn('"partnerCheckoutSetupRecoveryCount": partner_checkout_setup_recovery_count', admin)
        self.assertIn("checkout-return setup recovery opened", html)

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

    def test_admin_can_copy_a_complete_setup_invitation_without_sending_it(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn("Copy setup invitation", html)
        self.assertIn("copyPartnerOnboardingInvitation", html)
        self.assertIn("partner_onboarding_invitation_copied", html)
        self.assertIn("paste it into your own follow-up when appropriate", html)

    def test_admin_can_copy_a_saved_partner_checkout_invitation_without_sending_or_charging(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn("Copy checkout invitation", html)
        self.assertIn("copyPartnerCheckoutInvitation", html)
        self.assertIn("request_type: 'founding_partner_checkout'", html)
        self.assertIn("partner_checkout_invitation_copied", html)
        self.assertIn("does not email anyone or collect a payment", html)


if __name__ == "__main__":
    unittest.main()
