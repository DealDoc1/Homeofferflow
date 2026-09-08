import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1953 import build_signwell_fields_txr1953, render_txr_1953


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

    def test_signer_map_covers_each_named_buyer_and_seller(self):
        fields = build_signwell_fields_txr1953({
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
        })[0]
        self.assertEqual([field["recipient_id"] for field in fields], ["1", "3", "2", "4"])
        self.assertTrue(all(field["type"] == "signature" for field in fields))
        self.assertEqual(len({field["api_id"] for field in fields}), 4)

    def test_signing_render_leaves_signature_lines_clear(self):
        rendered = render_txr_1953(blank_one_page_pdf(), {
            "buyer_names": ["Buyer One"],
            "seller_names": ["Seller One"],
            "_for_signing": True,
        })
        extracted = PdfReader(io.BytesIO(rendered)).pages[0].extract_text()
        self.assertNotIn("Buyer One", extracted)
        self.assertNotIn("Seller One", extracted)

    def test_long_explanation_is_preserved_on_a_continuation_exhibit(self):
        explanation = " ".join(["Complete residential lease disclosure detail"] * 30)
        rendered = render_txr_1953(blank_one_page_pdf(), {
            "property_address": "1 Main Street, Sherman, TX 75090",
            "explanation": explanation,
        })
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("TXR-1953 CONTINUATION EXHIBIT", text)
        self.assertIn("Complete residential lease disclosure detail", text)


if __name__ == "__main__":
    unittest.main()
