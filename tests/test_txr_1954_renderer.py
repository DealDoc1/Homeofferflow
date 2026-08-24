import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1954 import render_txr_1954


def blank_one_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage(); canvas.save()
    return output.getvalue()


class Txr1954RendererTests(unittest.TestCase):
    def test_renderer_preserves_one_page_and_overlays_selected_values(self):
        rendered = render_txr_1954(blank_one_page_pdf(), {
            "property_address": "1438 Whitaker Road, Van Alstyne, TX",
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
            "leased_fixture_types": ["solar_panels", "other"],
            "leased_fixtures_other": "Pool equipment",
            "assumed_fixture_leases": ["solar_panels"],
            "buyer_first_cost": "2500",
            "removal_choice": "will_not",
            "delivery_choice": "oral_notice",
            "oral_fixture_lease_notice": "Solar lease with monthly payment and remaining term.",
        })
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        for expected in ("1438 Whitaker", "Buyer One", "Buyer Two", "Seller One", "Seller Two", "2500", "Pool equipment", "Solar lease"):
            self.assertIn(expected, text)

    def test_renderer_rejects_a_non_matching_source_length(self):
        output = io.BytesIO(); canvas = Canvas(output, pagesize=(612, 792)); canvas.showPage(); canvas.showPage(); canvas.save()
        with self.assertRaisesRegex(ValueError, "exactly one page"):
            render_txr_1954(output.getvalue(), {})


if __name__ == "__main__":
    unittest.main()
