import importlib.util
import unittest
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_dashboard_trec_62", ROOT / "api" / "admin-dashboard.py")
ADMIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADMIN)


def source_pdf():
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(612, 792))
    canvas.drawString(40, 70, "ADDITIONAL OPTION FEE RECEIPT")
    canvas.drawString(40, 50, "ADDITIONAL EARNEST MONEY RECEIPT")
    canvas.showPage()
    canvas.save()
    return stream.getvalue()


class Trec620FollowupTests(unittest.TestCase):
    def data(self):
        return {
            "property_address": "1438 Whitaker Road, Van Alstyne, TX",
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
            "delivery_date": "09/22/2026",
        }

    def test_parser_keeps_buyers_out_of_the_signature_recipient_list(self):
        parsed = ADMIN._parse_trec_62_0_draft({
            "formCode": "TREC-62-0",
            "formSourceId": "11111111-1111-4111-8111-111111111111",
            "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
            "buyerNames": ["Buyer One"],
            "sellerNames": ["Seller One", "Seller Two"],
            "deliveryDate": "2026-09-22",
            "sellerNoticeAcknowledgment": True,
        })
        self.assertEqual(parsed["client_names"], ["Seller One", "Seller Two"])
        self.assertEqual(parsed["agreement_data"]["buyer_names"], ["Buyer One"])
        self.assertEqual(parsed["agreement_data"]["delivery_date"], "09/22/2026")

    def test_renderer_populates_notice_and_preserves_escrow_receipt_sections(self):
        from lib.trec_62_0 import render_trec_62_0
        rendered = render_trec_62_0(source_pdf(), self.data())
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(rendered)).pages)
        for expected in (
            "1438 Whitaker Road, Van Alstyne, TX", "Buyer One and Buyer Two", "09/22/2026",
            "ADDITIONAL OPTION FEE RECEIPT", "ADDITIONAL EARNEST MONEY RECEIPT",
        ):
            self.assertIn(expected, text)

    def test_signing_map_is_seller_only_and_parallel(self):
        from lib.trec_62_0 import build_signwell_fields_trec620
        fields = build_signwell_fields_trec620(self.data())[0]
        self.assertEqual({field["recipient_id"] for field in fields}, {"1", "2"})
        self.assertEqual(sum(field["type"] == "signature" for field in fields), 2)
        self.assertEqual(sum(field["type"] == "date" for field in fields), 2)
        self.assertTrue(all(field["page"] == 1 for field in fields))

    def test_ui_is_guided_and_address_autocomplete_ready(self):
        asset = (ROOT / "assets" / "trec-62-followup.js").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn('name="propertyAddress"', asset)
        self.assertIn('autocomplete="street-address"', asset)
        self.assertIn("Date this notice will be delivered to Buyer", asset)
        self.assertIn("receipt sections remain blank for the escrow agent", asset)
        self.assertIn("Remove a backup-contract contingency", html)
        self.assertIn("Which purchase document does this transaction need?", html)
        self.assertIn("'/assets/trec-62-followup.js'", worker)

    def test_source_allowlist_and_database_constraint_include_form(self):
        uploader = (ROOT / "lib" / "platform_form_source_upload.py").read_text(encoding="utf-8")
        migration = (ROOT / "supabase" / "migrations" / "20260922125504_expand_trec_62_0_source_code.sql").read_text(encoding="utf-8")
        self.assertIn('"TREC-62-0"', uploader)
        self.assertIn("'TREC-62-0'", migration)


if __name__ == "__main__":
    unittest.main()
