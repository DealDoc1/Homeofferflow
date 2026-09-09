import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1914 import build_signwell_fields_txr1914, render_txr_1914


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
        "note_amount": "250000",
        "interest_rate": "6.25",
        "payment": {"plan": "monthly_installments", "installment_amount": "1800", "interest_style": "including_interest", "begins_after_months": "1", "payoff_after_months": "180"},
        "property_transfer": "consent_required",
        "casualty_insurance": "required",
        "escrow": {"choice": "required", "third_party_servicer": "will", "cost_paid_by": "buyer"},
    }


class Txr1914RendererTests(unittest.TestCase):
    def test_renderer_preserves_two_pages_and_overlays_review_terms(self):
        reader = PdfReader(io.BytesIO(render_txr_1914(blank_pdf(), sample_data())))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("1438 Whitaker", "Buyer One", "Seller Two", "250000", "6.25", "1800", "2025 tax return"):
            self.assertIn(expected, text)

    def test_renderer_rejects_non_matching_source_length(self):
        with self.assertRaisesRegex(ValueError, "exactly two pages"):
            render_txr_1914(blank_pdf(1), sample_data())

    def test_signwell_fields_follow_the_two_source_signature_rows(self):
        one_each = build_signwell_fields_txr1914({
            "buyer_names": ["Buyer One"],
            "seller_names": ["Seller One"],
        })[0]
        self.assertEqual(
            [(field["api_id"], field["page"], field["x"], field["y"], field["recipient_id"])
             for field in one_each],
            [
                ("txr1914_buyer1_signature_p2", 2, 55, 718, "1"),
                ("txr1914_seller1_signature_p2", 2, 415, 718, "2"),
            ],
        )

        two_each = build_signwell_fields_txr1914({
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
        })[0]
        self.assertEqual(
            [(field["api_id"], field["y"], field["recipient_id"])
             for field in two_each],
            [
                ("txr1914_buyer1_signature_p2", 718, "1"),
                ("txr1914_seller1_signature_p2", 718, "3"),
                ("txr1914_buyer2_signature_p2", 820, "2"),
                ("txr1914_seller2_signature_p2", 820, "4"),
            ],
        )

    def test_signwell_fields_require_named_parties(self):
        with self.assertRaisesRegex(ValueError, "one or two Buyers"):
            build_signwell_fields_txr1914({"buyer_names": [], "seller_names": ["Seller"]})


if __name__ == "__main__":
    unittest.main()
