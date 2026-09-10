import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "ai-offer-review.py"
SPEC = importlib.util.spec_from_file_location("broker_mls_context", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Response:
    status_code = 200

    def json(self):
        return {
            "listing": {
                "listingId": "NTX-123",
                "status": "Active",
                "listPrice": "500000",
                "daysOnMarket": 9,
                "priceChanges": "None",
                "marketEvidence": ["Active for 9 days."],
                "limitations": ["Confirm final status with the listing broker."],
            }
        }


class _Client:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, headers, json):
        self.url = url
        self.headers = headers
        self.body = json
        return _Response()


class BrokerMlsContextTests(unittest.TestCase):
    def setUp(self):
        self.original = (
            MODULE.ENABLE_BROKER_MLS_CONTEXT,
            MODULE.BROKER_MLS_CONTEXT_URL,
            MODULE.BROKER_MLS_CONTEXT_TOKEN,
        )

    def tearDown(self):
        (
            MODULE.ENABLE_BROKER_MLS_CONTEXT,
            MODULE.BROKER_MLS_CONTEXT_URL,
            MODULE.BROKER_MLS_CONTEXT_TOKEN,
        ) = self.original

    def test_is_off_without_an_explicit_broker_configuration(self):
        MODULE.ENABLE_BROKER_MLS_CONTEXT = False
        context = MODULE._broker_mls_property_context(
            {"propertyAddress": "100 Main Street"}, include_broker_mls_context=True
        )
        self.assertFalse(context["found"])
        self.assertEqual(context["reason"], "broker_mls_context_not_configured")

    def test_uses_one_server_side_proxy_lookup_when_explicitly_enabled(self):
        MODULE.ENABLE_BROKER_MLS_CONTEXT = True
        MODULE.BROKER_MLS_CONTEXT_URL = "https://mls-proxy.example.test/context"
        MODULE.BROKER_MLS_CONTEXT_TOKEN = "server-only-token"
        client = _Client()
        with patch.object(MODULE.httpx, "Client", return_value=client):
            context = MODULE._broker_mls_property_context(
                {"propertyAddress": "100 Main Street", "city": "Dallas", "state": "TX", "zip": "75201"},
                include_broker_mls_context=True,
            )
        self.assertTrue(context["found"])
        self.assertTrue(context["mlsVerified"])
        self.assertEqual(context["sourceType"], "broker_authorized_reso_mls")
        self.assertEqual(context["daysOnMarket"], 9)
        self.assertEqual(client.url, MODULE.BROKER_MLS_CONTEXT_URL)
        self.assertEqual(client.headers["Authorization"], "Bearer server-only-token")
        self.assertEqual(client.body["property"]["city"], "Dallas")
        self.assertNotIn("privateRemarks", client.body["fields"])

    def test_authorized_mls_context_skips_public_grounding(self):
        with patch.object(MODULE, "_broker_mls_property_context", return_value={"found": True, "sourceType": "broker_authorized_reso_mls"}), patch.object(MODULE, "_grounded_property_context") as public:
            selected = MODULE._select_property_context(
                {"propertyAddress": "100 Main Street"},
                include_broker_mls_context=True,
                include_public_context=True,
            )
        self.assertEqual(selected["sourceType"], "broker_authorized_reso_mls")
        public.assert_not_called()

    def test_offer_review_requests_the_broker_lookup_without_exposing_credentials(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("includeBrokerMlsContext: true", html)
        self.assertIn("approved RESO proxy", html)
        self.assertNotIn("BROKER_MLS_CONTEXT_TOKEN", html)


if __name__ == "__main__":
    unittest.main()
