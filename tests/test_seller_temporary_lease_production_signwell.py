import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "fill-pdf.py"


def load_offer_api():
    spec = importlib.util.spec_from_file_location("homeofferflow_offer_api_for_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seller_lease_offer():
    return {
        "userType": "agent",
        "buyer1": "Buyer One",
        "buyer2": "Buyer Two",
        "buyerEmail": "buyer1@example.com",
        "buyer2Email": "buyer2@example.com",
        "seller": "Seller One and Seller Two",
        "seller1Name": "Seller One",
        "seller1Email": "seller1@example.com",
        "seller2Name": "Seller Two",
        "seller2Email": "seller2@example.com",
        "sellerTemporaryLease": "yes",
        "possession": "sellerTemporaryLease",
        "address": "1438 Whitaker Road",
        "agentName": "Test Agent",
        "agentEmail": "agent@example.com",
    }


class SellerTemporaryLeaseProductionSignWellTests(unittest.TestCase):
    def test_invalid_seller_lease_recipient_email_is_rejected_before_signwell_delivery(self):
        api = load_offer_api()
        api.SIGNWELL_ENABLED = True
        api.SIGNWELL_API_KEY = "test_key"
        offer = seller_lease_offer()
        offer["seller1Email"] = "not-an-email"
        result = api.create_signwell_signature_request(offer, b"%PDF-test")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "Invalid seller email for SignWell")

    def test_browser_blocks_invalid_lease_signer_email_before_packet_generation(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        start = html.index("function validateSellerTemporaryLeaseInputs(data)")
        end = html.index("function confirmControlledLaunchSupport", start)
        validation = html[start:end]
        self.assertIn("const signerEmails = [", validation)
        self.assertIn("invalidSigner", validation)
        self.assertIn("needs a valid email address before HomeOfferFlow can create signature delivery.", validation)

    def test_seller_lease_uses_four_recipients_in_party_order(self):
        api = load_offer_api()
        api.SIGNWELL_ENABLED = True
        api.SIGNWELL_API_KEY = "test_key"
        api.build_signwell_fields = lambda offer, pdf: [[]]
        captured = {}

        def fake_post(payload):
            captured["payload"] = payload
            return True, {"id": "test-document"}

        api.post_signwell_document = fake_post
        result = api.create_signwell_signature_request(seller_lease_offer(), b"%PDF-test")

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "bundle_v13_seller_temporary_lease_multisigner")
        payload = captured["payload"]
        self.assertTrue(payload["apply_signing_order"])
        self.assertEqual(
            [(recipient["id"], recipient["email"]) for recipient in payload["recipients"]],
            [
                ("1", "buyer1@example.com"),
                ("2", "buyer2@example.com"),
                ("3", "seller1@example.com"),
                ("4", "seller2@example.com"),
            ],
        )
        self.assertEqual(payload["metadata"]["seller_temporary_lease_tenant_count"], "2")


if __name__ == "__main__":
    unittest.main()
