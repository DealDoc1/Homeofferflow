from io import BytesIO
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


if __name__ == "__main__":
    unittest.main()
