import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1953 import render_txr_1953


def blank_one_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage(); canvas.save()
    return output.getvalue()


class Txr1953RendererTests(unittest.TestCase):
    def test_renderer_preserves_one_page_and_overlays_selected_values(self):
        rendered = render_txr_1953(blank_one_page_pdf(), {
            "property_address": "1438 Whitaker Road, Van Alstyne, TX",
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
            "lease_status": "assignment",
            "delivery_choice": "not_received",
            "delivery_days": "3",
            "explanation": "No tenant disputes reported.",
        })
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        for expected in ("1438 Whitaker", "Buyer One", "Buyer Two", "Seller One", "Seller Two", "3", "No tenant disputes"):
            self.assertIn(expected, text)

    def test_renderer_rejects_a_non_matching_source_length(self):
        output = io.BytesIO(); canvas = Canvas(output, pagesize=(612, 792)); canvas.showPage(); canvas.showPage(); canvas.save()
        with self.assertRaisesRegex(ValueError, "exactly one page"):
            render_txr_1953(output.getvalue(), {})


if __name__ == "__main__":
    unittest.main()
