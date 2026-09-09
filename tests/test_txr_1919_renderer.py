import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1919 import build_signwell_fields_txr1919, render_txr_1919


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

    def test_signwell_fields_follow_the_two_source_signature_rows(self):
        one_each = build_signwell_fields_txr1919({
            "buyer_names": ["Buyer One"],
            "seller_names": ["Seller One"],
        })[0]
        self.assertEqual(
            [(field["api_id"], field["page"], field["x"], field["y"], field["recipient_id"])
             for field in one_each],
            [
                ("txr1919_buyer1_signature_p2", 2, 60, 656, "1"),
                ("txr1919_seller1_signature_p2", 2, 432, 656, "2"),
            ],
        )

        two_each = build_signwell_fields_txr1919({
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
        })[0]
        self.assertEqual(
            [(field["api_id"], field["y"], field["recipient_id"])
             for field in two_each],
            [
                ("txr1919_buyer1_signature_p2", 656, "1"),
                ("txr1919_seller1_signature_p2", 656, "3"),
                ("txr1919_buyer2_signature_p2", 739, "2"),
                ("txr1919_seller2_signature_p2", 739, "4"),
            ],
        )

    def test_signwell_fields_require_named_parties(self):
        with self.assertRaisesRegex(ValueError, "one or two Buyers"):
            build_signwell_fields_txr1919({"buyer_names": [], "seller_names": ["Seller"]})


if __name__ == "__main__":
    unittest.main()
