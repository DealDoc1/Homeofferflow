import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "lib" / "seller_checkout.py"
WEBHOOK_PATH = ROOT / "api" / "stripe-webhook" / "index.py"
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "migrations" / "20260910051231_seller_checkout_requests.sql").read_text(encoding="utf-8")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
SPEC = importlib.util.spec_from_file_location("seller_checkout", MODULE_PATH)
checkout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkout)
WEBHOOK_SPEC = importlib.util.spec_from_file_location("seller_checkout_webhook", WEBHOOK_PATH)
webhook = importlib.util.module_from_spec(WEBHOOK_SPEC)
WEBHOOK_SPEC.loader.exec_module(webhook)


class Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class Client:
    def __init__(self, response):
        self.response = response
        self.lookup_response = response
        self.posts = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def post(self, *args, **kwargs):
        self.posts.append((args, kwargs))
        return self.response

    async def get(self, *_args, **_kwargs):
        return self.lookup_response

    async def patch(self, *_args, **_kwargs):
        return self.response


class SellerCheckoutRequestTests(unittest.IsolatedAsyncioTestCase):
    lead_id = "e35eace9-2760-4b11-a01a-07ee65f2744e"

    def test_schema_and_workspace_limit_checkout_to_fixed_price_packages(self):
        self.assertIn("seller_checkout_status", MIGRATION)
        self.assertIn("hof_seller_leads_checkout_status_allowed", MIGRATION)
        self.assertIn("sellerLeadCheckoutAction", INDEX)
        self.assertIn("create_seller_checkout_request", INDEX)
        self.assertIn("Confirm that you reviewed the seller’s scope and fixed price", INDEX)

    def test_seller_payment_messages_prefer_the_verified_transactional_sender(self):
        self.assertIn('os.environ.get("RESEND_TRANSACTION_FROM_EMAIL")', MODULE_PATH.read_text(encoding="utf-8"))
        self.assertIn('os.environ.get("RESEND_TRANSACTION_FROM_EMAIL")', WEBHOOK_PATH.read_text(encoding="utf-8"))

    def test_checkout_return_explains_success_or_cancel_without_exposing_order_data(self):
        self.assertIn('id="sellerCheckoutContext"', SELLERS)
        self.assertIn("paymentState === 'success'", SELLERS)
        self.assertIn("we’re confirming your payment", SELLERS)
        self.assertIn("once payment confirmation is complete", SELLERS)
        self.assertIn("No payment was made.", SELLERS)
        self.assertIn("cleanUrl.searchParams.delete('seller_payment')", SELLERS)

    def test_admin_gets_a_safe_fallback_when_checkout_email_delivery_fails(self):
        self.assertIn("const checkoutUrl = String(result?.sellerCheckout?.checkoutUrl || '');", INDEX)
        self.assertIn("await navigator.clipboard.writeText(checkoutUrl)", INDEX)
        self.assertIn("window.prompt('Copy the secure seller payment link:', checkoutUrl)", INDEX)

    def test_admin_recovers_an_existing_link_without_creating_a_second_checkout_or_email(self):
        self.assertIn("recover_seller_checkout_request", INDEX)
        self.assertIn("Copy payment link", INDEX)
        self.assertIn("No new checkout or email was created.", INDEX)
        self.assertIn("async def recover_request(data):", checkout_source := MODULE_PATH.read_text(encoding="utf-8"))
        self.assertIn("https://api.stripe.com/v1/checkout/sessions/", checkout_source)

    def test_scope_confirmation_is_required(self):
        # This validates before database or payment-provider access.
        import asyncio
        with patch.object(checkout, "STRIPE_SECRET_KEY", "sk_test_x"):
            with self.assertRaisesRegex(ValueError, "Confirm the seller's scope"):
                asyncio.run(checkout.create_request({"seller_lead_id": self.lead_id}))

    async def test_server_selects_the_fixed_seller_prep_price(self):
        lead = {"id": self.lead_id, "seller_email": "seller@example.com", "service_level": "seller_prep", "status": "qualified", "seller_checkout_status": "not_requested"}
        session = {"id": "cs_live_abc12345", "url": "https://checkout.stripe.com/c/pay/cs_live_abc12345"}
        client = Client(Response(200, session))
        with patch.object(checkout, "STRIPE_SECRET_KEY", "sk_test_x"), \
             patch.object(checkout, "RESEND_API_KEY", ""), \
             patch.object(checkout.httpx, "AsyncClient", return_value=client):
            # The first client request is the lead lookup; give it lead data.
            client.lookup_response = Response(200, [lead])
            async def post(*args, **kwargs):
                client.posts.append((args, kwargs))
                return Response(200, session)
            client.post = post
            result = await checkout.create_request({"seller_lead_id": self.lead_id, "scope_confirmed": True})
        self.assertEqual(result["amountCents"], 29900)
        stripe_form = client.posts[0][1]["data"]
        self.assertEqual(stripe_form["line_items[0][price_data][unit_amount]"], "29900")
        self.assertEqual(stripe_form["metadata[seller_lead_id]"], self.lead_id)
        self.assertEqual(stripe_form["metadata[seller_package]"], "seller_prep")

    async def test_quote_based_seller_packages_cannot_create_checkout(self):
        lead = {"id": self.lead_id, "seller_email": "seller@example.com", "service_level": "flat_fee_mls", "status": "qualified", "seller_checkout_status": "not_requested"}
        client = Client(Response(200, [lead]))
        with patch.object(checkout.httpx, "AsyncClient", return_value=client), patch.object(checkout, "STRIPE_SECRET_KEY", "sk_test_x"):
            with self.assertRaisesRegex(PermissionError, "confirmed quote"):
                await checkout.create_request({"seller_lead_id": self.lead_id, "scope_confirmed": True})

    async def test_existing_seller_payment_request_cannot_create_a_second_checkout_link(self):
        lead = {
            "id": self.lead_id,
            "seller_email": "seller@example.com",
            "service_level": "seller_prep",
            "status": "qualified",
            "seller_checkout_status": "sent",
            "seller_checkout_session_id": "cs_live_existing",
        }
        client = Client(Response(200, [lead]))
        with patch.object(checkout.httpx, "AsyncClient", return_value=client), patch.object(checkout, "STRIPE_SECRET_KEY", "sk_test_x"):
            with self.assertRaisesRegex(PermissionError, "already been sent"):
                await checkout.create_request({"seller_lead_id": self.lead_id, "scope_confirmed": True})
        self.assertEqual(client.posts, [])

    async def test_existing_seller_payment_link_can_be_retrieved_without_creating_a_new_session(self):
        lead = {
            "id": self.lead_id,
            "service_level": "seller_prep",
            "status": "qualified",
            "seller_checkout_status": "sent",
            "seller_checkout_session_id": "cs_live_existing",
        }
        session = {"id": "cs_live_existing", "url": "https://checkout.stripe.com/c/pay/cs_live_existing"}
        class RecoveryClient(Client):
            def __init__(self):
                super().__init__(Response(200, [lead]))
                self.calls = 0

            async def get(self, *_args, **_kwargs):
                self.calls += 1
                return Response(200, [lead]) if self.calls == 1 else Response(200, session)

        client = RecoveryClient()
        with patch.object(checkout, "STRIPE_SECRET_KEY", "sk_test_x"), patch.object(checkout.httpx, "AsyncClient", return_value=client):
            result = await checkout.recover_request({"seller_lead_id": self.lead_id, "scope_confirmed": True})
        self.assertEqual(result["delivery"], "existing")
        self.assertEqual(result["checkoutUrl"], session["url"])
        self.assertEqual(client.posts, [])

    async def test_stripe_checkout_request_uses_a_stable_seller_idempotency_key(self):
        lead = {"id": self.lead_id, "seller_email": "seller@example.com", "service_level": "seller_prep", "status": "qualified", "seller_checkout_status": "not_requested"}
        session = {"id": "cs_live_abc12345", "url": "https://checkout.stripe.com/c/pay/cs_live_abc12345"}
        client = Client(Response(200, session))
        with patch.object(checkout, "STRIPE_SECRET_KEY", "sk_test_x"), \
             patch.object(checkout, "RESEND_API_KEY", ""), \
             patch.object(checkout.httpx, "AsyncClient", return_value=client):
            client.lookup_response = Response(200, [lead])
            async def post(*args, **kwargs):
                client.posts.append((args, kwargs))
                return Response(200, session)
            client.post = post
            await checkout.create_request({"seller_lead_id": self.lead_id, "scope_confirmed": True})
        self.assertEqual(client.posts[0][1]["headers"]["Idempotency-Key"], "seller-checkout-" + self.lead_id)

    async def test_unqualified_lead_cannot_create_checkout(self):
        lead = {"id": self.lead_id, "seller_email": "seller@example.com", "service_level": "seller_prep", "status": "new", "seller_checkout_status": "not_requested"}
        client = Client(Response(200, [lead]))
        with patch.object(checkout.httpx, "AsyncClient", return_value=client), patch.object(checkout, "STRIPE_SECRET_KEY", "sk_test_x"):
            with self.assertRaisesRegex(PermissionError, "Qualify the seller"):
                await checkout.create_request({"seller_lead_id": self.lead_id, "scope_confirmed": True})

    def test_completed_seller_checkout_routes_to_the_private_payment_recorder(self):
        request = webhook.handler.__new__(webhook.handler)
        captured = {}
        request._mark_seller_lead_paid = lambda lead_id, session: captured.update(lead_id=lead_id, session=session)
        request._handle_checkout_completed({"metadata": {"seller_lead_id": self.lead_id, "seller_package": "seller_prep"}, "payment_status": "paid"})
        self.assertEqual(captured["lead_id"], self.lead_id)

    def test_completed_seller_checkout_sends_one_idempotent_payment_receipt(self):
        class ReceiptResponse:
            status_code = 202
            text = ""

        class ReceiptClient:
            requests = []

            def __init__(self, *_args, **_kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def patch(self, url, **kwargs):
                ReceiptClient.requests.append(("patch", url, kwargs))
                return ReceiptResponse()

            def post(self, url, **kwargs):
                ReceiptClient.requests.append(("post", url, kwargs))
                return ReceiptResponse()

        request = webhook.handler.__new__(webhook.handler)
        ReceiptClient.requests = []
        session = {
            "id": "cs_live_receipt",
            "payment_intent": "pi_live_receipt",
            "payment_status": "paid",
            "customer_email": "seller@example.com",
            "metadata": {"seller_package": "seller_prep"},
        }
        with patch.object(webhook, "RESEND_API_KEY", "re_test"), patch.object(webhook.httpx, "Client", ReceiptClient):
            request._mark_seller_lead_paid(self.lead_id, session)
        email = next(entry for entry in ReceiptClient.requests if entry[0] == "post")
        self.assertEqual(email[1], "https://api.resend.com/emails")
        self.assertEqual(email[2]["json"]["to"], ["seller@example.com"])
        self.assertIn("Payment confirmed", email[2]["json"]["subject"])
        self.assertEqual(email[2]["json"]["tags"], [
            {"name": "email_type", "value": "seller_payment_receipt"},
            {"name": "seller_package", "value": "seller_prep"},
        ])
        self.assertEqual(email[2]["headers"]["Idempotency-Key"], "seller-payment-receipt-cs_live_receipt")

    def test_unpaid_seller_checkout_cannot_mutate_a_lead(self):
        request = webhook.handler.__new__(webhook.handler)
        with self.assertRaisesRegex(ValueError, "has not completed payment"):
            request._mark_seller_lead_paid(self.lead_id, {"metadata": {"seller_package": "seller_prep"}, "payment_status": "unpaid"})


if __name__ == "__main__":
    unittest.main()
