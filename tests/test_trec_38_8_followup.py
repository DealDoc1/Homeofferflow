import importlib.util
import unittest
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_dashboard_trec_38_8", ROOT / "api" / "admin-dashboard.py")
ADMIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADMIN)


def source_pdf():
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(612, 792))
    canvas.drawString(40, 70, "BUYER'S NOTICE OF TERMINATION OF CONTRACT")
    canvas.showPage()
    canvas.save()
    return stream.getvalue()


class Trec388FollowupTests(unittest.TestCase):
    def data(self):
        return {
            "property_address": "1438 Whitaker Road, Van Alstyne, TX",
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
            "termination_reasons": ["option_period", "other"],
            "other_termination_basis": "Paragraph 22 and the attached addendum.",
        }

    def test_parser_keeps_sellers_out_of_signature_recipients(self):
        parsed = ADMIN._parse_trec_38_8_draft({
            "formCode": "TREC-38-8",
            "formSourceId": "11111111-1111-4111-8111-111111111111",
            "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
            "buyerNames": ["Buyer One", "Buyer Two"],
            "sellerNames": ["Seller One"],
            "terminationReasons": ["option_period"],
            "otherTerminationBasis": "",
            "terminationAcknowledgment": True,
        })
        self.assertEqual(parsed["client_names"], ["Buyer One", "Buyer Two"])
        self.assertEqual(parsed["agreement_data"]["seller_names"], ["Seller One"])
        self.assertEqual(parsed["agreement_data"]["termination_reasons"], ["option_period"])

    def test_other_reason_requires_its_contract_basis(self):
        with self.assertRaisesRegex(ValueError, "contract paragraph or addendum"):
            ADMIN._parse_trec_38_8_draft({
                "formCode": "TREC-38-8",
                "formSourceId": "11111111-1111-4111-8111-111111111111",
                "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
                "buyerNames": ["Buyer One"],
                "sellerNames": ["Seller One"],
                "terminationReasons": ["other"],
                "otherTerminationBasis": "",
                "terminationAcknowledgment": True,
            })

    def test_renderer_populates_notice_and_marks_selected_reasons(self):
        from lib.trec_38_8 import render_trec_38_8
        rendered = render_trec_38_8(source_pdf(), self.data())
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(rendered)).pages)
        normalized = " ".join(text.split())
        for expected in (
            "1438 Whitaker Road, Van Alstyne, TX", "Seller One and Seller Two",
            "Paragraph 22 and the attached addendum.", "X",
        ):
            self.assertIn(expected, normalized)
        self.assertNotIn("Buyer One and Buyer Two", normalized)

    def test_signing_map_is_buyer_only_and_parallel(self):
        from lib.trec_38_8 import build_signwell_fields_trec388
        fields = build_signwell_fields_trec388(self.data())[0]
        self.assertEqual({field["recipient_id"] for field in fields}, {"1", "2"})
        self.assertEqual(sum(field["type"] == "signature" for field in fields), 2)
        self.assertEqual(sum(field["type"] == "date" for field in fields), 2)
        self.assertTrue(all(field["page"] == 1 for field in fields))

    def test_ui_is_guided_and_address_autocomplete_ready(self):
        asset = (ROOT / "assets" / "trec-38-8-followup.js").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn('name="propertyAddress"', asset)
        self.assertIn('autocomplete="street-address"', asset)
        self.assertIn("Why is the Buyer terminating?", asset)
        self.assertIn("release of earnest money is handled separately", asset)
        self.assertIn("End a purchase contract", html)
        self.assertIn("'/assets/trec-38-8-followup.js'", worker)

    def test_source_allowlist_and_database_constraint_include_form(self):
        uploader = (ROOT / "lib" / "platform_form_source_upload.py").read_text(encoding="utf-8")
        migration = (ROOT / "supabase" / "migrations" / "20260922141000_expand_trec_38_8_source_code.sql").read_text(encoding="utf-8")
        self.assertIn('"TREC-38-8"', uploader)
        self.assertIn("'TREC-38-8'", migration)


if __name__ == "__main__":
    unittest.main()
