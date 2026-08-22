import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1917 import render_txr_1917


def blank_pdf(pages=1):
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(pages):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


class Txr1917RendererTests(unittest.TestCase):
    def test_renderer_preserves_page_and_overlays_review_choices(self):
        data = {
            "property_address": "1438 Whitaker Road, Van Alstyne, TX",
            "review_types": ["environmental", "wetlands"],
            "termination_days": "10",
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
        }
        reader = PdfReader(io.BytesIO(render_txr_1917(blank_pdf(), data)))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        for expected in ("1438 Whitaker", "Buyer One", "Buyer Two", "Seller One", "Seller Two", "10"):
            self.assertIn(expected, text)

    def test_renderer_rejects_non_matching_source_length(self):
        with self.assertRaisesRegex(ValueError, "exactly one page"):
            render_txr_1917(blank_pdf(2), {})


if __name__ == "__main__":
    unittest.main()
