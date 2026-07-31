import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from api.txr_1507 import build_signwell_fields_txr1507, render_txr_1507


def blank_two_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage()
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "client_names": ["Test Buyer One", "Test Buyer Two"],
        "market_area": "1438 Whitaker Road, Van Alstyne, Grayson County, Texas 75495",
        "term_start": "2026-08-01",
        "term_end": "2027-01-31",
        "service_level": "full_services",
        "showing_fee": "",
        "compensation": {
            "purchase_percentage": "3",
            "purchase_flat_fee": "",
            "lease_one_month_percentage": "",
            "lease_total_rents_percentage": "",
            "lease_flat_fee": "",
        },
        "intermediary": "authorized",
    }


class Txr1507RendererTests(unittest.TestCase):
    def test_renderer_preserves_two_pages_and_overlays_only_supplied_values(self):
        rendered = render_txr_1507(
            blank_two_page_pdf(),
            sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"name": "Andrew Christian", "license_number": "0738821"},
        )
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("Test Buyer One, Test Buyer Two", "OnDemand Realty", "1438 Whitaker Road", "2026-08-01", "2027-01-31", "9010832", "Andrew Christian"):
            self.assertIn(expected, text)

    def test_signer_map_is_separate_for_one_and_two_clients(self):
        one = build_signwell_fields_txr1507(sample_data(), client_count=1)[0]
        two = build_signwell_fields_txr1507(sample_data(), client_count=2)[0]
        self.assertEqual(len(one), 3)
        self.assertEqual(len(two), 6)
        self.assertTrue(all(field["page"] in {1, 2} for field in two))
        self.assertTrue(all(field["recipient_id"] in {"1", "2"} for field in two))
        self.assertEqual({field["api_id"] for field in one}, {
            "txr1507_client1_initials_p1",
            "txr1507_client1_signature_p2",
            "txr1507_client1_date_p2",
        })


if __name__ == "__main__":
    unittest.main()
