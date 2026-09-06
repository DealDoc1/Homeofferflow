from io import BytesIO
import unittest

from pypdf import PdfReader

from api import representation_agreement as agreement
from pathlib import Path


class RepresentationAgreementTests(unittest.TestCase):
    def test_short_form_uses_only_explicit_interview_values(self):
        packet = agreement.build_short_form({
            "clientName": "Taylor Client",
            "brokerName": "OnDemand Realty",
            "brokerLicense": "123456",
            "associateName": "Morgan Agent",
            "associateLicense": "654321",
            "marketArea": "Collin and Grayson Counties, Texas",
            "startDate": "09/06/2026",
            "endDate": "12/31/2026",
            "serviceLevel": "full",
            "purchaseCompType": "percent",
            "purchaseCompValue": "3",
            "leaseCompType": "month_percent",
            "leaseCompValue": "25",
            "intermediaryAuthorized": "no",
        })
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Taylor Client", text)
        self.assertIn("Collin and Grayson Counties", text)
        self.assertIn("123456", text)

    def test_short_form_signature_fields_cover_client_and_broker(self):
        fields = agreement.build_short_form_signwell_fields({"clientTwoEmail": "two@example.com"})[0]
        by_id = {field["api_id"]: field for field in fields}
        self.assertEqual(by_id["client_signature"]["page"], 2)
        self.assertEqual(by_id["client_signature"]["y"], 505)
        self.assertEqual(by_id["broker_signature"]["recipient_id"], "2")
        self.assertEqual(by_id["client_two_signature"]["recipient_id"], "3")

    def test_endpoint_requires_the_core_interview_values(self):
        source = (Path(__file__).resolve().parents[1] / "api" / "representation-agreement.py").read_text()
        for field in ("clientName", "brokerName", "marketArea", "startDate", "endDate"):
            self.assertIn(field, source)
        self.assertIn("signature_requests_enabled\": False", source)

    def test_signature_payload_has_client_and_broker_recipients(self):
        payload = agreement.build_short_form_signwell_payload({
            "clientName": "Taylor Client",
            "clientEmail": "client@example.com",
            "brokerName": "OnDemand Realty",
            "brokerEmail": "broker@example.com",
        }, b"%PDF-test", test_mode=True)
        self.assertTrue(payload["test_mode"])
        self.assertEqual([recipient["id"] for recipient in payload["recipients"]], ["1", "2"])
        self.assertEqual(payload["fields"][0][0]["api_id"], "client_signature")


if __name__ == "__main__":
    unittest.main()
