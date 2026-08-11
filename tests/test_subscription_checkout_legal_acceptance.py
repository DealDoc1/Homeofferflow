import importlib.util
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PATH = ROOT / "api" / "create-subscription-checkout" / "index.py"
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "migrations" / "20260811113000_homeofferflow_subscription_checkout_legal_acceptance.sql").read_text(encoding="utf-8")

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_example")
os.environ.setdefault("STRIPE_AGENT_MONTHLY_PRICE_ID", "price_agent_monthly")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checkout = load_module("subscription_checkout_legal_acceptance", CHECKOUT_PATH)


class StripeClient:
    last_post = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        self.__class__.last_post = (url, kwargs)
        return type("Response", (), {"status_code": 200, "json": lambda self: {"url": "https://checkout.stripe.test/session"}, "text": ""})()


class SubscriptionCheckoutLegalAcceptanceTests(unittest.TestCase):
    def setUp(self):
        checkout.STRIPE_SECRET_KEY = "sk_test_example"
        checkout.AGENT_MONTHLY_PRICE_ID = "price_agent_monthly"
        StripeClient.last_post = None

    def request(self):
        raw = json.dumps({"plan": "agent", "billing": "monthly"}).encode()
        request = checkout.handler.__new__(checkout.handler)
        request.headers = {"Content-Length": str(len(raw)), "authorization": "Bearer verified-token", "origin": "https://preview.example.vercel.app"}
        request.rfile = io.BytesIO(raw)
        captured = {}
        request._json = lambda code, data: captured.update(code=code, data=data)
        request._require_supabase = lambda: None
        request._verified_user = lambda _header: {"id": "user-1", "email": "agent@example.test"}
        request._has_current_subscription = lambda _user_id: False
        return request, captured

    def test_checkout_rejects_direct_request_without_current_legal_acceptance(self):
        request, captured = self.request()
        request._has_current_legal_acceptance = lambda _user_id: False
        with patch.object(checkout.httpx, "Client", StripeClient):
            request.do_POST()
        self.assertEqual(captured["code"], 403)
        self.assertIn("Accept the current Terms", captured["data"]["error"])
        self.assertIsNone(StripeClient.last_post)

    def test_checkout_allows_current_legal_acceptance(self):
        request, captured = self.request()
        request._has_current_legal_acceptance = lambda _user_id: True
        with patch.object(checkout.httpx, "Client", StripeClient):
            request.do_POST()
        self.assertEqual(captured["code"], 200)
        self.assertIsNotNone(StripeClient.last_post)

    def test_browser_prompts_then_persists_before_standard_subscription_checkout(self):
        self.assertIn("ensureCurrentLegalAcceptanceForSubscription", INDEX)
        self.assertIn("subscriptionLegalConsentModal", INDEX)
        self.assertIn("recordCurrentLegalAcceptance('subscription_checkout')", INDEX)
        self.assertIn("if (!await ensureCurrentLegalAcceptanceForSubscription())", INDEX)

    def test_migration_allows_the_distinct_subscription_checkout_source(self):
        self.assertIn("drop constraint if exists hof_legal_acceptances_source_check", MIGRATION)
        self.assertIn("subscription_checkout", MIGRATION)


if __name__ == "__main__":
    unittest.main()
