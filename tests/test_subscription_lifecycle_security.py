import importlib.util
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PATH = ROOT / "api" / "create-subscription-checkout" / "index.py"
PORTAL_PATH = ROOT / "api" / "create-billing-portal" / "index.py"
WEBHOOK_PATH = ROOT / "api" / "stripe-webhook" / "index.py"
LEDGER_MIGRATION = ROOT / "supabase" / "homeofferflow_stripe_webhook_event_ledger.sql"
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_example")
os.environ.setdefault("STRIPE_AGENT_MONTHLY_PRICE_ID", "price_agent_monthly")
os.environ.setdefault("STRIPE_AGENT_ANNUAL_PRICE_ID", "price_agent_annual")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-test-key")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checkout = load_module("subscription_lifecycle_checkout", CHECKOUT_PATH)
portal = load_module("subscription_lifecycle_portal", PORTAL_PATH)
webhook = load_module("subscription_lifecycle_webhook", WEBHOOK_PATH)


class Response:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


class CheckoutStripeClient:
    last_post = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        self.__class__.last_post = (url, kwargs)
        return Response(200, {"id": "cs_test", "url": "https://checkout.stripe.test/session"})


class BillingClient:
    last_portal_post = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, **kwargs):
        if url.endswith("/auth/v1/user"):
            return Response(200, {"id": "real-user", "email": "real@example.com"})
        if url.endswith("/rest/v1/hof_subscriptions"):
            return Response(200, [{"stripe_customer_id": "cus_real_account"}])
        raise AssertionError(f"Unexpected GET {url}")

    def post(self, url, **kwargs):
        self.__class__.last_portal_post = (url, kwargs)
        return Response(200, {"id": "bps_test", "url": "https://billing.stripe.test/session"})


class WebhookLedgerClient:
    insert_rows = [{"stripe_event_id": "evt_new"}]
    existing_state = "processed"
    requests = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        self.__class__.requests.append(("post", url, kwargs))
        return Response(201, self.__class__.insert_rows)

    def get(self, url, **kwargs):
        self.__class__.requests.append(("get", url, kwargs))
        return Response(200, [{"processing_state": self.__class__.existing_state}])

    def patch(self, url, **kwargs):
        self.__class__.requests.append(("patch", url, kwargs))
        return Response(204, [])


class SubscriptionLifecycleSecurityTests(unittest.TestCase):
    def setUp(self):
        checkout.STRIPE_SECRET_KEY = "sk_test_example"
        checkout.AGENT_MONTHLY_PRICE_ID = "price_agent_monthly"
        checkout.AGENT_ANNUAL_PRICE_ID = "price_agent_annual"
        checkout.SUPABASE_URL = "https://example.supabase.co"
        checkout.SUPABASE_SERVICE_ROLE_KEY = "service-test-key"
        portal.STRIPE_SECRET_KEY = "sk_test_example"
        portal.SUPABASE_URL = "https://example.supabase.co"
        portal.SUPABASE_SERVICE_ROLE_KEY = "service-test-key"
        webhook.STRIPE_WEBHOOK_SECRET = "whsec_test_example"
        os.environ.pop("STRIPE_WEBHOOK_ALLOW_TEST_EVENTS", None)
        os.environ.pop("STRIPE_WEBHOOK_TEST_ENVIRONMENT", None)
        os.environ.pop("VERCEL_ENV", None)
        CheckoutStripeClient.last_post = None
        BillingClient.last_portal_post = None
        WebhookLedgerClient.insert_rows = [{"stripe_event_id": "evt_new"}]
        WebhookLedgerClient.existing_state = "processed"
        WebhookLedgerClient.requests = []

    def _checkout_request(self, body, authorization="Bearer verified-token"):
        raw = json.dumps(body).encode()
        request = checkout.handler.__new__(checkout.handler)
        request.headers = {
            "Content-Length": str(len(raw)),
            "origin": "https://www.homeofferflow.com",
            "authorization": authorization,
        }
        request.rfile = io.BytesIO(raw)
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        return request, captured

    def test_standard_checkout_rejects_missing_session_before_stripe(self):
        request, captured = self._checkout_request(
            {"plan": "agent", "email": "someone@example.com", "userId": "someone-else"},
            authorization="",
        )
        request._verified_user = lambda _header: None
        with patch.object(checkout.httpx, "Client", CheckoutStripeClient):
            request.do_POST()
        self.assertEqual(captured["code"], 401)
        self.assertIsNone(CheckoutStripeClient.last_post)

    def test_standard_checkout_uses_identity_from_verified_session(self):
        request, captured = self._checkout_request(
            {"plan": "agent", "billing": "monthly", "email": "attacker@example.com", "userId": "attacker-id"}
        )
        request._verified_user = lambda _header: {"id": "real-user", "email": "real@example.com"}
        request._has_current_subscription = lambda _user_id: False
        with patch.object(checkout.httpx, "Client", CheckoutStripeClient):
            request.do_POST()
        self.assertEqual(captured["code"], 200)
        form = CheckoutStripeClient.last_post[1]["data"]
        self.assertEqual(form["customer_email"], "real@example.com")
        self.assertEqual(form["metadata[user_id]"], "real-user")
        self.assertEqual(form["metadata[email]"], "real@example.com")

    def test_billing_portal_derives_customer_from_authenticated_account(self):
        raw = json.dumps(
            {
                "customerId": "cus_another_customer",
                "returnUrl": "https://evil.example/redirect",
            }
        ).encode()
        request = portal.handler.__new__(portal.handler)
        request.headers = {"Content-Length": str(len(raw)), "authorization": "Bearer verified-token"}
        request.rfile = io.BytesIO(raw)
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        with patch.object(portal.httpx, "Client", BillingClient):
            request.do_POST()
        self.assertEqual(captured["code"], 200)
        form = BillingClient.last_portal_post[1]["data"]
        self.assertEqual(form["customer"], "cus_real_account")
        self.assertEqual(form["return_url"], "https://www.homeofferflow.com/")

    def test_billing_portal_rejects_missing_session(self):
        raw = b"{}"
        request = portal.handler.__new__(portal.handler)
        request.headers = {"Content-Length": str(len(raw)), "authorization": ""}
        request.rfile = io.BytesIO(raw)
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        request._verified_user = lambda _header: None
        request.do_POST()
        self.assertEqual(captured["code"], 401)

    def test_browser_sends_session_token_to_checkout_and_billing(self):
        self.assertIn("'Authorization': 'Bearer ' + accessToken", INDEX_HTML)
        self.assertNotIn("customerId,\n          returnUrl", INDEX_HTML)

    def test_paid_trial_invoice_keeps_current_trialing_status(self):
        request = webhook.handler.__new__(webhook.handler)
        captured = {}
        request._iso_now = lambda: "2026-07-29T00:00:00Z"
        request._stripe_get_subscription = lambda _subscription_id: {
            "id": "sub_trial",
            "customer": "cus_trial",
            "status": "trialing",
            "trial_end": 1785379200,
            "items": {"data": [{"price": {"id": "price_agent_monthly"}}]},
        }
        request._patch_subscription_by_stripe_subscription_id = (
            lambda subscription_id, payload: captured.update(subscription_id=subscription_id, payload=payload)
        )
        request._handle_invoice_status({"subscription": "sub_trial"}, "active")
        self.assertEqual(captured["subscription_id"], "sub_trial")
        self.assertEqual(captured["payload"]["status"], "trialing")
        self.assertIn("trial_ends_at", captured["payload"])

    def test_invoice_paid_event_dispatches_the_same_safe_access_refresh(self):
        event = {
            "type": "invoice.paid",
            "data": {"object": {"subscription": "sub_paid"}},
        }
        raw = json.dumps(event).encode()
        request = webhook.handler.__new__(webhook.handler)
        request.headers = {"Content-Length": str(len(raw)), "Stripe-Signature": "test"}
        request.rfile = io.BytesIO(raw)
        request._verify_stripe_signature = lambda *_args: True
        captured = {}
        request._handle_invoice_status = lambda invoice, status: captured.update(
            invoice=invoice, status=status
        )
        request._send_json = lambda *_args: None

        request.do_POST()

        self.assertEqual(captured["invoice"]["subscription"], "sub_paid")
        self.assertEqual(captured["status"], "active")

    def test_stripe_test_mode_event_cannot_mutate_production_by_default(self):
        event = {
            "livemode": False,
            "type": "invoice.paid",
            "data": {"object": {"subscription": "sub_sandbox"}},
        }
        raw = json.dumps(event).encode()
        request = webhook.handler.__new__(webhook.handler)
        request.headers = {"Content-Length": str(len(raw)), "Stripe-Signature": "test"}
        request.rfile = io.BytesIO(raw)
        request._verify_stripe_signature = lambda *_args: True
        request._handle_invoice_status = lambda *_args: self.fail(
            "Sandbox events must not update the production subscription."
        )
        captured = {}
        request._send_json = lambda code, data: captured.update(code=code, data=data)

        request.do_POST()

        self.assertEqual(captured["code"], 400)
        self.assertEqual(captured["data"]["error"], "Stripe test events are not accepted here.")

    def test_isolated_test_environment_may_explicitly_process_sandbox_events(self):
        event = {
            "livemode": False,
            "type": "invoice.paid",
            "data": {"object": {"subscription": "sub_sandbox"}},
        }
        raw = json.dumps(event).encode()
        request = webhook.handler.__new__(webhook.handler)
        request.headers = {"Content-Length": str(len(raw)), "Stripe-Signature": "test"}
        request.rfile = io.BytesIO(raw)
        request._verify_stripe_signature = lambda *_args: True
        captured = {}
        request._handle_invoice_status = lambda invoice, status: captured.update(
            invoice=invoice, status=status
        )
        request._send_json = lambda *_args: None

        with patch.dict(
            os.environ,
            {
                "STRIPE_WEBHOOK_ALLOW_TEST_EVENTS": "true",
                "VERCEL_ENV": "preview",
                "STRIPE_WEBHOOK_TEST_ENVIRONMENT": "preview",
            },
        ):
            request.do_POST()

        self.assertEqual(captured["invoice"]["subscription"], "sub_sandbox")
        self.assertEqual(captured["status"], "active")

    def test_production_never_accepts_sandbox_events_even_if_the_flag_is_set(self):
        event = {
            "livemode": False,
            "type": "invoice.paid",
            "data": {"object": {"subscription": "sub_sandbox"}},
        }
        raw = json.dumps(event).encode()
        request = webhook.handler.__new__(webhook.handler)
        request.headers = {"Content-Length": str(len(raw)), "Stripe-Signature": "test"}
        request.rfile = io.BytesIO(raw)
        request._verify_stripe_signature = lambda *_args: True
        request._handle_invoice_status = lambda *_args: self.fail(
            "Production must never process Stripe sandbox events."
        )
        captured = {}
        request._send_json = lambda code, data: captured.update(code=code, data=data)

        with patch.dict(
            os.environ,
            {
                "STRIPE_WEBHOOK_ALLOW_TEST_EVENTS": "true",
                "VERCEL_ENV": "production",
                "STRIPE_WEBHOOK_TEST_ENVIRONMENT": "production",
            },
        ):
            request.do_POST()

        self.assertEqual(captured["code"], 400)
        self.assertEqual(captured["data"]["error"], "Stripe test events are not accepted here.")

    def test_webhook_ledger_deduplicates_completed_events_without_storing_event_body(self):
        request = webhook.handler.__new__(webhook.handler)
        request._iso_now = lambda: "2026-07-29T00:00:00Z"
        event = {"id": "evt_completed", "livemode": True}
        data = {"subscription": "sub_completed", "customer": "cus_completed"}

        WebhookLedgerClient.insert_rows = []
        WebhookLedgerClient.existing_state = "processed"
        with patch.object(webhook.httpx, "Client", WebhookLedgerClient):
            self.assertFalse(request._claim_webhook_event("evt_completed", "invoice.paid", event, data))

        self.assertEqual(WebhookLedgerClient.requests[0][0], "post")
        self.assertEqual(WebhookLedgerClient.requests[1][0], "get")
        stored = WebhookLedgerClient.requests[0][2]["json"]
        self.assertEqual(stored["stripe_event_id"], "evt_completed")
        self.assertNotIn("data", stored)
        self.assertNotIn("customer_email", stored)

    def test_webhook_ledger_records_processing_result_and_allows_failed_retry(self):
        request = webhook.handler.__new__(webhook.handler)
        request._iso_now = lambda: "2026-07-29T00:00:00Z"
        event = {"id": "evt_retry", "livemode": True}

        WebhookLedgerClient.insert_rows = []
        WebhookLedgerClient.existing_state = "failed"
        with patch.object(webhook.httpx, "Client", WebhookLedgerClient):
            self.assertTrue(request._claim_webhook_event("evt_retry", "invoice.paid", event, {}))
            request._record_webhook_event("evt_retry", "processed")

        patch_payloads = [entry[2]["json"] for entry in WebhookLedgerClient.requests if entry[0] == "patch"]
        self.assertEqual(patch_payloads[0]["processing_state"], "received")
        self.assertEqual(patch_payloads[1]["processing_state"], "processed")
        self.assertIn("processed_at", patch_payloads[1])

    def test_webhook_ledger_is_server_only(self):
        migration = LEDGER_MIGRATION.read_text(encoding="utf-8")
        self.assertIn("enable row level security", migration)
        self.assertIn("revoke all on table public.hof_stripe_webhook_events from anon, authenticated", migration)
        self.assertIn("grant all on table public.hof_stripe_webhook_events to service_role", migration)

    def test_platform_admin_can_monitor_webhook_delivery_without_customer_or_payment_data(self):
        admin_source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("stripeWebhookEvents", admin_source)
        self.assertIn(
            "select=stripe_event_id,event_type,livemode,processing_state,error_code,received_at,processed_at",
            admin_source,
        )
        self.assertNotIn("hof_stripe_webhook_events?select=*", admin_source)
        for sensitive in ("customer_email", "payment_method", "card_last4", "event_payload"):
            self.assertNotIn(sensitive, admin_source)
        self.assertIn("Billing Webhook Activity", INDEX_HTML)

    def test_webhook_failure_does_not_expose_internal_error_text(self):
        event = {"type": "checkout.session.completed", "data": {"object": {}}}
        raw = json.dumps(event).encode()
        request = webhook.handler.__new__(webhook.handler)
        request.headers = {"Content-Length": str(len(raw)), "Stripe-Signature": "test"}
        request.rfile = io.BytesIO(raw)
        request._verify_stripe_signature = lambda *_args: True
        request._handle_checkout_completed = lambda *_args: (_ for _ in ()).throw(
            RuntimeError("internal upstream diagnostic")
        )
        captured = {}
        request._send_json = lambda code, data: captured.update(code=code, data=data)

        with patch("builtins.print"):
            request.do_POST()

        self.assertEqual(captured["code"], 500)
        self.assertEqual(captured["data"]["error"], "Webhook processing failed.")
        self.assertNotIn("diagnostic", captured["data"]["error"])

    def test_failed_invoice_immediately_marks_subscription_past_due(self):
        request = webhook.handler.__new__(webhook.handler)
        captured = {}
        request._iso_now = lambda: "2026-07-29T00:00:00Z"
        request._stripe_get_subscription = lambda _subscription_id: {
            "id": "sub_payment_failed",
            "customer": "cus_payment_failed",
            "status": "active",
            "items": {"data": [{"price": {"id": "price_agent_monthly"}}]},
        }
        request._patch_subscription_by_stripe_subscription_id = (
            lambda subscription_id, payload: captured.update(subscription_id=subscription_id, payload=payload)
        )
        request._handle_invoice_status({"subscription": "sub_payment_failed"}, "past_due")
        self.assertEqual(captured["payload"]["status"], "past_due")

    def test_deleted_subscription_is_recorded_as_canceled(self):
        request = webhook.handler.__new__(webhook.handler)
        captured = {}
        request._iso_now = lambda: "2026-07-29T00:00:00Z"
        request._upsert_subscription_by_user_id = lambda payload: captured.update(payload=payload)
        request._activate_brokerage_membership = lambda *_args: self.fail(
            "A canceled subscription must not activate brokerage membership."
        )

        request._handle_subscription_event(
            {
                "id": "sub_canceled",
                "customer": "cus_canceled",
                "status": "canceled",
                "metadata": {"user_id": "user-canceled", "plan": "agent", "role": "agent"},
                "items": {"data": [{"price": {"id": "price_agent_monthly"}}]},
            },
            "customer.subscription.deleted",
        )

        self.assertEqual(captured["payload"]["status"], "canceled")
        self.assertEqual(captured["payload"]["stripe_subscription_id"], "sub_canceled")
        self.assertFalse(captured["payload"]["cancel_at_period_end"])

    def test_scheduled_cancellation_keeps_access_until_the_saved_end_date(self):
        request = webhook.handler.__new__(webhook.handler)
        captured = {}
        request._iso_now = lambda: "2026-07-29T00:00:00Z"
        request._upsert_subscription_by_user_id = lambda payload: captured.update(payload=payload)
        request._activate_brokerage_membership = lambda *_args: captured.update(
            brokerage_membership_activated=True
        )

        request._handle_subscription_event(
            {
                "id": "sub_scheduled_cancel",
                "customer": "cus_scheduled_cancel",
                "status": "active",
                "cancel_at_period_end": True,
                "cancel_at": 1782777600,
                "metadata": {
                    "user_id": "user-scheduled-cancel",
                    "email": "agent@ondemand.test",
                    "plan": "agent",
                    "role": "agent",
                    "brokerage_id": "ondemand-brokerage",
                },
                "items": {"data": [{"price": {"id": "price_agent_monthly"}}]},
            },
            "customer.subscription.updated",
        )

        self.assertEqual(captured["payload"]["status"], "active")
        self.assertTrue(captured["payload"]["cancel_at_period_end"])
        self.assertEqual(captured["payload"]["cancel_at"], "2026-06-30T00:00:00Z")
        self.assertTrue(captured["brokerage_membership_activated"])

    def test_checkout_does_not_activate_brokerage_membership_for_a_non_active_subscription(self):
        request = webhook.handler.__new__(webhook.handler)
        captured = {}
        request._stripe_get_subscription = lambda _subscription_id: {
            "id": "sub_incomplete",
            "customer": "cus_incomplete",
            "status": "incomplete",
            "metadata": {
                "user_id": "user-incomplete",
                "email": "agent@ondemand.test",
                "brokerage_id": "ondemand-brokerage",
                "launch_source": "ondemand",
            },
            "items": {"data": [{"price": {"id": "price_agent_monthly"}}]},
        }
        request._upsert_subscription_by_user_id = lambda payload: captured.update(payload=payload)
        request._activate_brokerage_membership = lambda *_args: self.fail(
            "A non-active subscription must not activate brokerage membership."
        )

        request._handle_checkout_completed({
            "subscription": "sub_incomplete",
            "customer": "cus_incomplete",
            "metadata": {"brokerage_id": "ondemand-brokerage"},
        })

        self.assertEqual(captured["payload"]["status"], "past_due")
        self.assertEqual(captured["payload"]["brokerage_id"], "ondemand-brokerage")

    def test_account_ui_discloses_trial_renewal_and_scheduled_cancellation(self):
        self.assertIn("Free trial active through", INDEX_HTML)
        self.assertIn("renews at $29/month", INDEX_HTML)
        self.assertIn("Cancellation scheduled.", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
