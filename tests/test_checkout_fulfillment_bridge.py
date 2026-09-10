import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
WEBHOOK_PATH = ROOT / "api" / "stripe-webhook" / "index.py"
FULFILLMENT_PATH = ROOT / "api" / "fill-pdf.py"

os.environ.setdefault("STRIPE_SUBSCRIPTION_WEBHOOK_SECRET", "whsec_bridge_test")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


webhook = load_module("checkout_fulfillment_webhook", WEBHOOK_PATH)
fulfillment = load_module("checkout_fulfillment_packet_service", FULFILLMENT_PATH)


class Response:
    status_code = 200


class CapturingClient:
    requests = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        self.__class__.requests.append((url, kwargs))
        return Response()


class CheckoutFulfillmentBridgeTests(unittest.TestCase):
    def setUp(self):
        CapturingClient.requests = []

    def test_paid_buyer_checkout_is_signed_and_forwarded_to_existing_packet_service(self):
        request = webhook.handler.__new__(webhook.handler)
        session = {
            "id": "cs_paid_buyer",
            "customer_email": "buyer@example.test",
            "metadata": {
                "plan": "self",
                "offer_parts": "1",
                "offer_0": '{"address":"123 Main Street"}',
            },
        }

        with patch.object(webhook, "INTERNAL_CHECKOUT_FORWARD_SECRET", "bridge-secret"), \
             patch.object(webhook, "PUBLIC_APP_ORIGIN", "https://www.homeofferflow.test"), \
             patch.object(webhook.httpx, "Client", CapturingClient):
            request._handle_checkout_completed(session)

        self.assertEqual(len(CapturingClient.requests), 1)
        url, kwargs = CapturingClient.requests[0]
        self.assertEqual(url, "https://www.homeofferflow.test/api/fill-pdf.py")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        body = kwargs["content"]
        event = json.loads(body.decode("utf-8"))
        self.assertEqual(event["type"], "checkout.session.completed")
        self.assertEqual(event["data"]["object"]["id"], "cs_paid_buyer")
        self.assertTrue(
            fulfillment.verify_internal_checkout_forward_signature(
                body,
                kwargs["headers"]["X-HomeOfferFlow-Checkout-Signature"],
                "bridge-secret",
            )
        )

    def test_expired_or_invalid_internal_handoff_signature_is_rejected(self):
        body = b'{"type":"checkout.session.completed"}'
        self.assertFalse(
            fulfillment.verify_internal_checkout_forward_signature(
                body, "t=1,v1=not-a-real-signature", "bridge-secret"
            )
        )

    def test_partner_and_seller_checkouts_never_enter_buyer_packet_fulfillment(self):
        request = webhook.handler.__new__(webhook.handler)
        forwarded = []
        request._forward_checkout_fulfillment = lambda *_args: forwarded.append(True)
        paid_partner = []
        request._mark_partner_lead_paid = lambda lead_id, _session: paid_partner.append(lead_id)
        request._handle_checkout_completed({
            "metadata": {"partner_lead_id": "partner-1", "plan": "self", "offer_parts": "1"},
        })
        self.assertEqual(paid_partner, ["partner-1"])
        self.assertEqual(forwarded, [])

        request._mark_seller_lead_paid = lambda lead_id, _session: paid_partner.append(lead_id)
        request._handle_checkout_completed({
            "metadata": {"seller_lead_id": "seller-1", "plan": "self", "offer_parts": "1"},
        })
        self.assertEqual(paid_partner[-1], "seller-1")
        self.assertEqual(forwarded, [])


if __name__ == "__main__":
    unittest.main()
