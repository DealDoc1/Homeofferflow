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
    def test_tiers_use_server_only_price_env_names(self):
        self.assertEqual(partner_checkout.PRICE_ENV_BY_TIER["founding_pilot"], "STRIPE_FOUNDING_PARTNER_LISTING_PRICE_ID")
        self.assertEqual(partner_checkout.PRICE_ENV_BY_TIER["monthly_placement"], "STRIPE_FOUNDING_PARTNER_FEATURED_PRICE_ID")
        self.assertEqual(partner_checkout.PRICE_ENV_BY_TIER["market_exclusive"], "STRIPE_FOUNDING_PARTNER_PREMIER_PRICE_ID")
        self.assertEqual(partner_checkout.MONTHLY_PRICE_ENV_BY_TIER["founding_pilot"], "STRIPE_FOUNDING_PARTNER_LISTING_MONTHLY_PRICE_ID")
        self.assertEqual(partner_checkout.MONTHLY_PRICE_ENV_BY_TIER["monthly_placement"], "STRIPE_FOUNDING_PARTNER_FEATURED_MONTHLY_PRICE_ID")
        self.assertEqual(partner_checkout.MONTHLY_PRICE_ENV_BY_TIER["market_exclusive"], "STRIPE_FOUNDING_PARTNER_PREMIER_MONTHLY_PRICE_ID")

    def test_checkout_origin_uses_request_host_not_a_redirect_parameter(self):
        self.assertEqual(partner_checkout._partner_checkout_origin({"host": "preview-homeofferflow.vercel.app", "x-forwarded-proto": "https"}), "https://preview-homeofferflow.vercel.app")
        self.assertEqual(partner_checkout._partner_checkout_origin({"host": "bad.example/path"}), "https://www.homeofferflow.com")

    def test_checkout_reads_existing_partner_lead_from_central_table(self):
        Client.requests = []
        with patch.object(partner_checkout.httpx, "Client", Client):
            lead = partner_checkout._get_partner_lead_for_checkout("e35eace9-2760-4b11-a01a-07ee65f2744e")
        self.assertEqual(lead["contact_email"], "partner@example.com")
        self.assertIn("hof_partner_leads", Client.requests[0][1])

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

    def test_partner_checkout_collects_launch_charge_and_defers_recurring_plan_for_90_days(self):
        Client.requests = []
        with patch.object(partner_checkout, "_get_partner_lead_for_checkout", return_value={
            "id": "e35eace9-2760-4b11-a01a-07ee65f2744e",
            "preferred_model": "monthly_placement",
            "contact_email": "partner@example.com",
            "status": "approved",
        }), patch.object(partner_checkout, "_mark_partner_checkout_started"), patch.object(partner_checkout.httpx, "Client", Client):
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


if __name__ == "__main__":
    unittest.main()
