from io import BytesIO
import unittest

from pypdf import PdfReader

from api import representation_long_form as agreement


class RepresentationLongFormTests(unittest.TestCase):
    def test_long_form_allows_omitted_optional_terms(self):
        """A partly completed interview still produces the complete packet."""
        packet = agreement.build_long_form({"clientName": "Taylor Client"})
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 6)

    def test_long_form_fills_explicit_core_and_advanced_values(self):
        packet = agreement.build_long_form({
            "clientName": "Taylor Client", "clientTwoName": "Jordan Client",
            "clientAddress": "123 Main Street", "clientCityStateZip": "Dallas, TX 75201",
            "clientPhone": "214-555-0100", "clientEmail": "taylor@example.com",
            "brokerName": "OnDemand Realty", "brokerLicense": "123456",
            "associateName": "Morgan Agent", "associateLicense": "654321",
            "marketArea": "Collin and Grayson Counties, Texas",
            "startDate": "09/06/2026", "endDate": "12/31/2026",
            "purchaseCompType": "percent", "purchaseCompValue": "3",
            "leaseCompType": "month_percent", "leaseCompValue": "25",
            "protectionPeriodDays": "30", "paymentCounty": "Collin",
            "relocationBenefitProvider": "Example Relocation", "intermediaryAuthorized": "no",
            "includeConsumerNotice": "yes",
        })
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 6)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for value in ("Taylor Client", "OnDemand Realty", "Collin and Grayson Counties", "Example Relocation", "123456"):
            self.assertIn(value, text)

    def test_signwell_payload_includes_required_initials_and_signatures(self):
        payload = agreement.build_long_form_signwell_payload({
            "clientName": "Taylor Client", "clientEmail": "taylor@example.com",
            "clientTwoName": "Jordan Client", "clientTwoEmail": "jordan@example.com",
            "brokerName": "OnDemand Realty", "brokerEmail": "broker@example.com",
        }, b"sample", test_mode=True)
        fields = payload["fields"][0]
        self.assertEqual(len(payload["recipients"]), 3)
        self.assertEqual(payload["metadata"]["agreement_type"], "TXR-1501-long-form")
        self.assertEqual(next(field for field in fields if field["api_id"] == "client_initials_1")["page"], 1)
        self.assertEqual(next(field for field in fields if field["api_id"] == "client_two_signature")["page"], 6)


if __name__ == "__main__":
    unittest.main()
