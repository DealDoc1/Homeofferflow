import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from api.txr_1501 import build_signwell_fields_txr1501, render_txr_1501


def blank_six_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(6):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "client_names": ["Test Buyer One", "Test Buyer Two"],
        "client_address": "721 Broderick Lane",
        "client_city_state_zip": "Prosper, TX 75078",
        "client_phone": "2143649890",
        "client_email": "buyer@example.com",
        "market_area": "Collin and Denton Counties, Texas",
        "term_start": "2026-08-01",
        "term_end": "2027-01-31",
        "compensation": {"purchase_percentage": "3"},
        "retainer_amount": "",
        "retainer_treatment": "",
        "protection_days": "30",
        "payment_county": "Collin",
        "intermediary": "authorized",
        "signer_plan": "clients_only",
    }


class Txr1501RendererTests(unittest.TestCase):
    def test_renderer_preserves_six_pages_and_overlays_supplied_values(self):
        rendered = render_txr_1501(
            blank_six_page_pdf(),
            sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"name": "Andrew Christian", "license_number": "0738821"},
        )
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 6)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("Test Buyer One, Test Buyer Two", "OnDemand Realty", "Collin and Denton Counties, Texas", "2026-08-01", "2027-01-31", "9010832", "Andrew Christian"):
            self.assertIn(expected, text)

    def test_signer_map_requires_plan_and_supports_one_or_two_clients(self):
        one = build_signwell_fields_txr1501({**sample_data(), "signer_plan": "clients_only"}, client_count=1)[0]
        two = build_signwell_fields_txr1501({**sample_data(), "signer_plan": "clients_only"}, client_count=2)[0]
        self.assertEqual(len(one), 2)
        self.assertEqual(len(two), 4)
        self.assertTrue(all(field["page"] == 6 for field in two))
        self.assertEqual({field["api_id"] for field in one}, {"txr1501_client1_signature_p6", "txr1501_client1_date_p6"})
        with self.assertRaisesRegex(ValueError, "Choose who will sign"):
            build_signwell_fields_txr1501({**sample_data(), "signer_plan": ""}, client_count=1)


if __name__ == "__main__":
    unittest.main()
