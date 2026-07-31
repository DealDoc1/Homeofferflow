import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from api.txr_1508 import build_signwell_fields_txr1508, render_txr_1508


def blank_one_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "property_address": "1438 Whitaker Road, Van Alstyne, TX",
        "client_names": ["Test Customer One", "Test Customer Two"],
        "other_broker_agreement": ["no", "yes"],
        "signer_plan": "associate_and_clients",
    }


class Txr1508RendererTests(unittest.TestCase):
    def test_renderer_preserves_one_page_and_overlays_scope_limited_values(self):
        rendered = render_txr_1508(
            blank_one_page_pdf(), sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"name": "Andrew Christian", "license_number": "0738821"},
        )
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        for expected in ("1438 Whitaker Road, Van Alstyne, TX", "Test Customer One", "Test Customer Two", "OnDemand Realty", "Andrew Christian"):
            self.assertIn(expected, text)

    def test_signer_map_is_explicit_for_one_or_two_customers(self):
        one = build_signwell_fields_txr1508({**sample_data(), "signer_plan": "broker_and_clients"}, client_count=1)[0]
        two = build_signwell_fields_txr1508(sample_data(), client_count=2)[0]
        self.assertEqual(len(one), 4)
        self.assertEqual(len(two), 6)
        self.assertTrue(all(field["page"] == 1 for field in two))
        with self.assertRaisesRegex(ValueError, "broker or associate"):
            build_signwell_fields_txr1508({**sample_data(), "signer_plan": ""}, client_count=1)


if __name__ == "__main__":
    unittest.main()
