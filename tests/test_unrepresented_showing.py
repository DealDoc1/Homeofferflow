from io import BytesIO
import json
from pathlib import Path
import unittest

from pypdf import PdfReader

from api import unrepresented_showing as showing


class UnrepresentedShowingTests(unittest.TestCase):
    def test_showing_form_uses_only_collected_details(self):
        packet = showing.build_showing_form({
            "propertyAddress": "1438 Whitaker Road, Dallas, Texas",
            "customerName": "Taylor Customer",
            "customerTwoName": "Jordan Customer",
            "customerHasRepresentation": "yes",
            "brokerName": "OnDemand Realty",
            "brokerLicense": "123456",
            "associateName": "Morgan Agent",
            "associateLicense": "654321",
        })
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        for value in ("1438 Whitaker Road", "Taylor Customer", "Jordan Customer", "OnDemand Realty", "123456"):
            self.assertIn(value, text)

    def test_endpoint_requires_showing_and_broker_details(self):
        source = (Path(__file__).resolve().parents[1] / "api" / "unrepresented-showing.py").read_text()
        for field in ("propertyAddress", "customerName", "brokerName", "associateName"):
            self.assertIn(field, source)

    def test_agent_workspace_has_a_compact_showing_interview(self):
        source = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        for token in (
            "Prepare a Neutral Showing Form",
            "downloadUnrepresentedShowingForm",
            "showingAgreementAddress",
            "/api/unrepresented-showing",
        ):
            self.assertIn(token, source)
        self.assertIn("['showingAgreementAddress', null]", source)

    def test_vercel_bundles_the_showing_form_with_its_endpoint(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "vercel.json").read_text())
        self.assertEqual(
            config["functions"]["api/unrepresented-showing.py"]["includeFiles"],
            "unrepresented_customer_showing_form_1508.pdf",
        )
        self.assertTrue((root / "unrepresented_customer_showing_form_1508.pdf").is_file())

    def test_agent_dashboard_starts_with_transaction_routing(self):
        source = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        for token in (
            "What are you working on?",
            "startAgentTransaction('listing')",
            "startAgentTransaction('purchase')",
            "startAgentTransaction('lease_listing')",
            "startAgentTransaction('lease_representation')",
        ):
            self.assertIn(token, source)
        self.assertIn("Agent Transaction Path Selected", source)

    def test_lease_listing_path_collects_lease_specific_details(self):
        source = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        for token in (
            "sellerListingIntent",
            "sellerLeadMonthlyRent",
            "updateSellerListingIntent",
            "Monthly rent:",
        ):
            self.assertIn(token, source)

    def test_showing_checkout_fallback_is_customer_friendly(self):
        source = (Path(__file__).resolve().parents[1] / "index.html").read_text()
        self.assertIn("Showing bookings are temporarily unavailable.", source)
        self.assertNotIn("Stripe setup needed.", source)


if __name__ == "__main__":
    unittest.main()
