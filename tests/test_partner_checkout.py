import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PATH = ROOT / "api" / "fsbo-lead.py"
WEBHOOK_PATH = ROOT / "api" / "stripe-webhook" / "index.py"

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_example")
os.environ.setdefault("STRIPE_FOUNDING_PARTNER_FEATURED_PRICE_ID", "price_featured")
os.environ.setdefault("STRIPE_FOUNDING_PARTNER_FEATURED_MONTHLY_PRICE_ID", "price_featured_monthly")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


partner_checkout = load_module("partner_checkout", CHECKOUT_PATH)
stripe_webhook = load_module("partner_stripe_webhook", WEBHOOK_PATH)


class Response:
    def __init__(self, status_code=200, payload=None, text="[]"):
        self.status_code = status_code
        self._payload = payload if payload is not None else []
        self.text = text

    def json(self):
        return self._payload


class Client:
    requests = []
    post_response = {"url": "https://checkout.stripe.test/session"}

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, **kwargs):
        Client.requests.append(("get", url, kwargs))
        return Response(payload=[{"id": "e35eace9-2760-4b11-a01a-07ee65f2744e", "preferred_model": "monthly_placement", "contact_email": "partner@example.com"}])

    def patch(self, url, **kwargs):
        Client.requests.append(("patch", url, kwargs))
        return Response(status_code=204, text="")

    def post(self, url, **kwargs):
        Client.requests.append(("post", url, kwargs))
        return Response(payload=Client.post_response, text='{"url":"https://checkout.stripe.test/session"}')


class PartnerCheckoutTests(unittest.TestCase):

    def test_cancelled_checkout_can_resume_without_reentering_saved_application(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("const hasSavedPartnerApplication = Boolean(window.__hofFoundingPartnerLeadId);", html)
        self.assertIn("if (!hasSavedPartnerApplication && (!hasType || !hasCompany || !hasContact || !hasEmail || !hasValidEmail || !hasMarket))", html)
        self.assertIn("if (!hasSavedPartnerApplication && !document.getElementById('foundingPartnerConsent')?.checked)", html)
        self.assertIn("source: hasSavedPartnerApplication ? 'partner_cancel_recovery' : payload.source", html)
        self.assertIn("checkout_source: hasSavedPartnerApplication ? 'partner_cancel_recovery' : ''", html)
        self.assertIn("You do not need to re-enter your saved essentials", html)

    def test_saved_application_state_is_clear_after_a_refresh_not_just_the_cancel_return(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function applySavedPartnerApplicationState()", html)
        self.assertIn("Resume Secure Checkout — saved application", html)
        self.assertIn("hasSavedApplication && window.__hofFoundingPartnerCheckoutState !== 'success'", html)
        self.assertIn("jump.style.display = hasSavedApplication ? 'none' : ''", html)

    def test_success_confirmation_provides_a_direct_safe_support_recovery_link(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="foundingPartnerCheckoutConfirmation"', html)
        self.assertIn('mailto:support@homeofferflow.com?subject=Partner%20setup%20link%20request', html)
        self.assertIn('ask support to issue a fresh secure link', html)
    def test_success_return_explains_secure_setup_timeline_and_activation_boundary(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("your next step is partner setup", html)
        self.assertIn("it expires in 14 days", html)
        self.assertIn("Setup does not activate advertising by itself.", html)
        self.assertIn("issue a fresh secure link", html)

    def test_tiers_use_server_only_price_env_names(self):
        self.assertEqual(partner_checkout.PRICE_ENV_BY_TIER["founding_pilot"], "STRIPE_FOUNDING_PARTNER_LISTING_PRICE_ID")
        self.assertEqual(partner_checkout.PRICE_ENV_BY_TIER["monthly_placement"], "STRIPE_FOUNDING_PARTNER_FEATURED_PRICE_ID")
        self.assertEqual(partner_checkout.PRICE_ENV_BY_TIER["market_exclusive"], "STRIPE_FOUNDING_PARTNER_PREMIER_PRICE_ID")
        self.assertEqual(partner_checkout.MONTHLY_PRICE_ENV_BY_TIER["founding_pilot"], "STRIPE_FOUNDING_PARTNER_LISTING_MONTHLY_PRICE_ID")
        self.assertEqual(partner_checkout.MONTHLY_PRICE_ENV_BY_TIER["monthly_placement"], "STRIPE_FOUNDING_PARTNER_FEATURED_MONTHLY_PRICE_ID")
        self.assertEqual(partner_checkout.MONTHLY_PRICE_ENV_BY_TIER["market_exclusive"], "STRIPE_FOUNDING_PARTNER_PREMIER_MONTHLY_PRICE_ID")

    def test_custom_partner_request_cannot_enter_a_price_based_checkout(self):
        with patch.object(partner_checkout, "STRIPE_SECRET_KEY", "sk_test_example"), patch.object(partner_checkout, "_get_partner_lead_for_checkout", return_value={
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "preferred_model": "discuss",
            "contact_email": "partner@example.com",
            "status": "new",
        }):
            with self.assertRaisesRegex(ValueError, "Custom and multi-market requests"):
                partner_checkout._create_partner_checkout("e35eace9-2760-4b11-a01a-07ee65f2744e", {})

    def test_checkout_origin_uses_request_host_not_a_redirect_parameter(self):
        self.assertEqual(partner_checkout._partner_checkout_origin({"host": "preview-homeofferflow.vercel.app", "x-forwarded-proto": "https"}), "https://preview-homeofferflow.vercel.app")
        self.assertEqual(partner_checkout._partner_checkout_origin({"host": "bad.example/path"}), "https://www.homeofferflow.com")

    def test_checkout_reads_existing_partner_lead_from_central_table(self):
        Client.requests = []
        with patch.object(partner_checkout.httpx, "Client", Client):
            lead = partner_checkout._get_partner_lead_for_checkout("e35eace9-2760-4b11-a01a-07ee65f2744e")
        self.assertEqual(lead["contact_email"], "partner@example.com")
        self.assertIn("hof_partner_leads", Client.requests[0][1])

    def test_partner_checkout_telemetry_is_aggregate_only(self):
        Client.requests = []
        with patch.object(partner_checkout.httpx, "Client", Client):
            partner_checkout._record_partner_checkout_event(
                "founding_partner_stripe_checkout_opened",
                "opened",
                "Partner secure checkout opened.",
                {"tier": "monthly_placement"},
            )
        request = Client.requests[0]
        self.assertEqual(request[0], "post")
        self.assertIn("hof_offer_events", request[1])
        telemetry = request[2]["json"]
        self.assertEqual(telemetry["offer_id"], None)
        self.assertEqual(telemetry["user_id"], None)
        self.assertEqual(telemetry["metadata"], {"tier": "monthly_placement"})
        self.assertNotIn("partner_lead_id", telemetry["metadata"])
        self.assertNotIn("contact_email", telemetry["metadata"])

    def test_paid_checkout_moves_existing_lead_to_ready_onboarding(self):
        calls = []
        webhook = stripe_webhook.handler.__new__(stripe_webhook.handler)
        with patch.object(webhook, "_require_supabase"), patch.object(stripe_webhook.httpx, "Client", Client):
            Client.requests = []
            webhook._mark_partner_lead_paid("e35eace9-2760-4b11-a01a-07ee65f2744e", {"id": "cs_test", "payment_intent": "pi_test", "customer": "cus_test"})
            calls = Client.requests
        self.assertEqual(calls[0][0], "patch")
        self.assertIn("hof_partner_leads", calls[0][1])
        self.assertEqual(calls[0][2]["json"]["payment_status"], "paid")
        self.assertEqual(calls[0][2]["json"]["onboarding_status"], "ready")
        self.assertTrue(calls[0][2]["json"]["onboarding_token_hash"])
        self.assertTrue(calls[0][2]["json"]["onboarding_token_expires_at"])

    def test_paid_checkout_records_privacy_safe_setup_invitation_telemetry(self):
        webhook = stripe_webhook.handler.__new__(stripe_webhook.handler)
        with patch.object(webhook, "_require_supabase"), \
             patch.object(webhook, "_deliver_partner_onboarding_email", return_value="sent"), \
             patch.object(webhook, "_record_partner_onboarding_event") as record, \
             patch.object(stripe_webhook.httpx, "Client", Client):
            webhook._mark_partner_lead_paid(
                "e35eace9-2760-4b11-a01a-07ee65f2744e",
                {"id": "cs_test", "payment_intent": "pi_test", "customer": "cus_test"},
            )
        self.assertEqual(record.call_count, 2)
        record.assert_any_call(
            "founding_partner_checkout_completed",
            "completed",
            "Partner secure checkout completed.",
            {"surface": "stripe_webhook"},
        )
        record.assert_any_call(
            "partner_onboarding_setup_issued",
            "sent",
            "Partner secure setup access issued after paid checkout.",
            {"surface": "stripe_webhook", "delivery": "sent"},
        )

    def test_paid_checkout_sends_setup_link_only_when_email_delivery_is_configured(self):
        webhook = stripe_webhook.handler.__new__(stripe_webhook.handler)
        with patch.object(stripe_webhook, "RESEND_API_KEY", "re_test"), patch.object(stripe_webhook.httpx, "Client", Client):
            Client.requests = []
            webhook._deliver_partner_onboarding_email({"customer_email": "partner@example.com"}, "A" * 32, "2026-08-20T00:00:00+00:00")
        email = next(request for request in Client.requests if request[0] == "post")
        self.assertEqual(email[1], "https://api.resend.com/emails")
        self.assertEqual(email[2]["json"]["to"], ["partner@example.com"])
        self.assertIn("partner_onboarding=", email[2]["json"]["text"])
        self.assertIn("does not activate advertising", email[2]["json"]["text"])

    def test_setup_email_reports_when_delivery_is_not_configured(self):
        webhook = stripe_webhook.handler.__new__(stripe_webhook.handler)
        with patch.object(stripe_webhook, "RESEND_API_KEY", ""):
            outcome = webhook._deliver_partner_onboarding_email(
                {"customer_email": "partner@example.com"}, "A" * 32, "2026-08-20T00:00:00+00:00"
            )
        self.assertEqual(outcome, "not_configured")

    def test_partner_checkout_collects_launch_charge_and_defers_recurring_plan_for_90_days(self):
        Client.requests = []
        with patch.object(partner_checkout, "_get_partner_lead_for_checkout", return_value={
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "preferred_model": "monthly_placement",
            "contact_email": "partner@example.com",
            "status": "approved",
        }), patch.object(partner_checkout, "_claim_partner_checkout_session", return_value={"id": "e35eace9-2760-4b11-a01a-07ee65f2744e"}) as claim_session, patch.object(partner_checkout, "_record_partner_checkout_event") as record, patch.object(partner_checkout.httpx, "Client", Client):
            result = partner_checkout._create_partner_checkout(
                "e35eace9-2760-4b11-a01a-07ee65f2744e",
                {"host": "www.homeofferflow.com", "x-forwarded-proto": "https"},
            )
        self.assertEqual(result, "https://checkout.stripe.test/session")
        post = next(request for request in Client.requests if request[0] == "post")
        form = post[2]["data"]
        self.assertEqual(form["mode"], "subscription")
        self.assertEqual(form["line_items[0][price]"], "price_featured")
        self.assertEqual(form["line_items[1][price]"], "price_featured_monthly")
        self.assertEqual(form["subscription_data[trial_period_days]"], "90")
        self.assertEqual(form["payment_method_collection"], "always")
        self.assertNotIn("cancel_at", form)
        self.assertIn("partner_resume_token=", form["cancel_url"])
        claim_session.assert_called_once()
        record.assert_called_once_with(
            "founding_partner_stripe_checkout_opened",
            "opened",
            "Partner secure checkout opened.",
            {"tier": "monthly_placement"},
        )

    def test_partner_checkout_rejects_identical_launch_and_renewal_prices(self):
        Client.requests = []
        with patch.dict(partner_checkout.os.environ, {
            "STRIPE_FOUNDING_PARTNER_FEATURED_PRICE_ID": "price_same",
            "STRIPE_FOUNDING_PARTNER_FEATURED_MONTHLY_PRICE_ID": "price_same",
        }, clear=False), patch.object(partner_checkout, "_get_partner_lead_for_checkout", return_value={
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "preferred_model": "monthly_placement",
            "contact_email": "partner@example.com",
            "status": "approved",
        }), patch.object(partner_checkout.httpx, "Client", Client):
            with self.assertRaisesRegex(RuntimeError, "same launch and renewal price"):
                partner_checkout._create_partner_checkout(
                    "e35eace9-2760-4b11-a01a-07ee65f2744e",
                    {"host": "www.homeofferflow.com", "x-forwarded-proto": "https"},
                )
        self.assertFalse(any(request[0] == "post" and "checkout/sessions" in request[1] for request in Client.requests))

    def test_checkout_reuses_a_still_open_stripe_session_before_creating_another(self):
        lead = {
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "preferred_model": "monthly_placement",
            "contact_email": "partner@example.com",
            "status": "approved",
            "payment_status": "checkout_started",
            "stripe_checkout_session_id": "cs_open",
        }
        with patch.object(partner_checkout, "_get_partner_lead_for_checkout", return_value=lead), \
             patch.object(partner_checkout, "_open_stripe_checkout_url", return_value="https://checkout.stripe.test/open"), \
             patch.object(partner_checkout, "_record_partner_checkout_event") as record, \
             patch.object(partner_checkout, "_claim_partner_checkout_session") as claim_session:
            result = partner_checkout._create_partner_checkout(lead["id"], {"host": "www.homeofferflow.com"})
        self.assertEqual(result, "https://checkout.stripe.test/open")
        claim_session.assert_not_called()
        record.assert_called_once_with(
            "founding_partner_stripe_checkout_opened",
            "opened",
            "Partner returned to an existing secure checkout.",
            {"tier": "monthly_placement"},
        )

    def test_checkout_recovery_records_only_the_allowlisted_aggregate_source(self):
        lead = {
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "preferred_model": "monthly_placement",
            "contact_email": "partner@example.com",
            "status": "approved",
            "payment_status": "checkout_started",
            "stripe_checkout_session_id": "cs_open",
        }
        with patch.object(partner_checkout, "_get_partner_lead_for_checkout", return_value=lead), \
             patch.object(partner_checkout, "_open_stripe_checkout_url", return_value="https://checkout.stripe.test/open"), \
             patch.object(partner_checkout, "_record_partner_checkout_event") as record:
            partner_checkout._create_partner_checkout(lead["id"], {"host": "www.homeofferflow.com"}, "partner_cancel_recovery")
        record.assert_called_once_with(
            "founding_partner_stripe_checkout_opened",
            "opened",
            "Partner returned to an existing secure checkout.",
            {"tier": "monthly_placement", "source": "partner_cancel_recovery"},
        )

    def test_checkout_session_claim_requires_same_unpaid_row_and_returns_claimed_row(self):
        Client.requests = []
        with patch.object(partner_checkout.httpx, "Client", Client):
            claimed = partner_checkout._claim_partner_checkout_session(
                "e35eace9-2760-4b11-a01a-07ee65f2744e", None,
                "e35eace9-2760-4b11-a01a-07ee65f2744e", "cs_new",
            )
        request = Client.requests[0]
        self.assertEqual(request[0], "patch")
        self.assertIn("payment_status=neq.paid", request[1])
        self.assertIn("stripe_checkout_session_id=is.null", request[1])
        self.assertEqual(request[2]["json"]["stripe_checkout_session_id"], "cs_new")
        self.assertIsNone(claimed)

    def test_checkout_return_requires_matching_lead_and_nonce(self):
        Client.requests = []
        with patch.object(partner_checkout.httpx, "Client", Client):
            partner_checkout._mark_partner_checkout_returned(
                "e35eace9-2760-4b11-a01a-07ee65f2744e",
                "e35eace9-2760-4b11-a01a-07ee65f2744e",
            )
        request = Client.requests[0]
        self.assertEqual(request[0], "patch")
        self.assertIn("checkout_resume_token", request[1])
        self.assertIn("payment_status=eq.checkout_started", request[1])


if __name__ == "__main__":
    unittest.main()
