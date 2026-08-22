import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1905 import render_txr_1905


def blank_one_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def blank_two_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage()
    canvas.showPage()
    canvas.save()
    return output.getvalue()


class Txr1905RendererTests(unittest.TestCase):
    def test_renderer_preserves_one_page_and_overlays_selected_values(self):
        rendered = render_txr_1905(blank_one_page_pdf(), {
            "property_address": "1438 Whitaker Road, Van Alstyne, TX",
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
            "reservation_choice": "undivided_interest",
            "undivided_interest": "25",
            "surface_rights": "not_waived",
        })
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        for expected in ("1438 Whitaker", "Buyer One", "Buyer Two", "Seller One", "Seller Two", "25"):
            self.assertIn(expected, text)

    def test_renderer_rejects_a_non_matching_source_length(self):
        with self.assertRaisesRegex(ValueError, "exactly one page"):
            render_txr_1905(blank_two_page_pdf(), {})


if __name__ == "__main__":
    unittest.main()
