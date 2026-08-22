import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1919 import render_txr_1919


def blank_pdf(pages=2):
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(pages):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "property_address": "1438 Whitaker Road, Van Alstyne, TX",
        "buyer_names": ["Buyer One", "Buyer Two"],
        "seller_names": ["Seller One", "Seller Two"],
        "credit_days": "7",
        "credit_documents": ["credit_report", "employment", "other"],
        "credit_other": "2025 tax return",
        "loans": {
            "first": {"enabled": True, "lender": "Example Bank", "balance": "240000", "monthly_payment": "1750"},
            "second": {"enabled": True, "lender": "Second Bank", "balance": "30000", "monthly_payment": "300"},
        },
        "variance": {"adjustment": "cash", "termination_threshold": "2500"},
        "loan_terms": {"first_fee_cap": "500", "second_fee_cap": "100", "first_rate_cap": "6.5", "second_rate_cap": "8"},
    }


class Txr1919RendererTests(unittest.TestCase):
    def test_renderer_preserves_two_pages_and_overlays_review_terms(self):
        reader = PdfReader(io.BytesIO(render_txr_1919(blank_pdf(), sample_data())))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("1438 Whitaker", "Buyer One", "Seller Two", "Example Bank", "Second Bank", "240000", "2025 tax return"):
            self.assertIn(expected, text)

    def test_renderer_rejects_non_matching_source_length(self):
        with self.assertRaisesRegex(ValueError, "exactly two pages"):
            render_txr_1919(blank_pdf(1), sample_data())


if __name__ == "__main__":
    unittest.main()
