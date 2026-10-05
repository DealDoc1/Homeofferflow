import hashlib
import importlib.util
import unittest
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests" / "fixtures" / "trec_39_11_source.pdf"
SPEC = importlib.util.spec_from_file_location("admin_dashboard_trec_39_11", ROOT / "api" / "admin-dashboard.py")
ADMIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADMIN)


class Trec3911AmendmentTests(unittest.TestCase):
    def payload(self):
        return {
            "formCode": "TREC-39-11",
            "formSourceId": "11111111-1111-4111-8111-111111111111",
            "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX",
            "buyerNames": ["Buyer One", "Buyer Two"],
            "sellerNames": ["Seller One", "Seller Two"],
            "changes": [
                "sales_price", "repairs", "closing_date", "seller_expense",
                "settlement_expenses", "lender_repairs", "option_extension",
                "buyer_approval_date", "other",
            ],
            "priceCash": "125000",
            "priceFinancing": "375000",
            "repairsText": "Remove the detached shed and haul away all resulting debris.",
            "closingDate": "2026-11-20",
            "sellerExpense": "7500",
            "settlementExpenses": {
                "seller": {"type": "amount", "value": "5500"},
                "buyer": {"type": "percent", "value": "1.25"},
            },
            "lenderRepairSeller": "2000",
            "lenderRepairBuyer": "0",
            "optionFee": "250",
            "optionExtensionDate": "2026-10-12",
            "optionFeeCredited": True,
            "buyerApprovalDate": "2026-10-28",
            "otherModifications": "The title company is changed to the office identified in the attached contract file.",
            "amendmentReviewAcknowledgment": True,
        }

    def parsed(self):
        return ADMIN._parse_trec_39_11_draft(self.payload())

    def test_official_source_is_current_exact_one_page_fixture(self):
        content = SOURCE.read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(), "d12909bcbd014080948eb6f9771231ba1b1d98c64eaf07e87ab0faa1118b8d36")
        reader = PdfReader(BytesIO(content))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        self.assertIn("TREC NO. 39-11", text)
        self.assertIn("This form replaces TREC No. 39-10", text)

    def test_parser_keeps_all_parties_in_parallel_recipient_order_and_calculates_total(self):
        parsed = self.parsed()
        self.assertEqual(parsed["client_names"], ["Buyer One", "Buyer Two", "Seller One", "Seller Two"])
        self.assertEqual(parsed["agreement_data"]["sales_price"]["total"], "500000.00")
        self.assertEqual(parsed["agreement_data"]["closing_date"], "11/20/2026")
        self.assertEqual(parsed["agreement_data"]["option_extension"]["date"], "10/12/2026")

    def test_parser_rejects_contradictory_option_choices(self):
        payload = self.payload()
        payload["changes"] = ["option_extension", "option_waiver"]
        with self.assertRaisesRegex(ValueError, "either an option-period extension or a waiver"):
            ADMIN._parse_trec_39_11_draft(payload)

    def test_renderer_populates_selected_terms_and_preserves_source(self):
        from lib.trec_39_11 import render_trec_39_11

        data = self.parsed()["agreement_data"]
        rendered = render_trec_39_11(SOURCE.read_bytes(), data)
        reader = PdfReader(BytesIO(rendered))
        self.assertEqual(len(reader.pages), 1)
        text = " ".join((reader.pages[0].extract_text() or "").split())
        for expected in (
            "TREC NO. 39-11", "1438 Whitaker Road, Van Alstyne, TX",
            "125,000.00", "375,000.00", "500,000.00", "November 20",
            "Remove the detached shed", "The title company is changed",
        ):
            self.assertIn(expected, text)

    def test_signing_map_uses_all_buyers_and_sellers_without_signing_order(self):
        from lib.trec_39_11 import build_signwell_fields_trec3911

        data = self.parsed()["agreement_data"]
        fields = build_signwell_fields_trec3911(data)[0]
        signatures = [field for field in fields if field["type"] == "signature"]
        self.assertEqual([field["recipient_id"] for field in signatures], ["1", "2", "3", "4"])
        self.assertEqual(len(signatures), 4)
        self.assertTrue(all(field["page"] == 1 for field in signatures))
        self.assertFalse(any(field["type"] == "date" for field in fields))

    def test_single_buyer_and_seller_use_the_first_printed_signature_lines(self):
        from lib.trec_39_11 import build_signwell_fields_trec3911

        data = self.parsed()["agreement_data"]
        data["buyer_names"] = ["Buyer One"]
        data["seller_names"] = ["Seller One"]
        signatures = [
            field for field in build_signwell_fields_trec3911(data)[0]
            if field["type"] == "signature"
        ]
        self.assertEqual(
            [(field["api_id"], field["recipient_id"], field["x"], field["y"]) for field in signatures],
            [
                ("trec3911_buyer1_signature_p1", "1", 48, 790),
                ("trec3911_seller1_signature_p1", "2", 419, 790),
            ],
        )

    def test_option_waiver_branch_needs_no_extension_answers(self):
        payload = self.payload()
        payload["changes"] = ["option_waiver"]
        payload["optionFee"] = ""
        payload["optionExtensionDate"] = ""
        parsed = ADMIN._parse_trec_39_11_draft(payload)
        self.assertEqual(parsed["agreement_data"]["changes"], ["option_waiver"])
        self.assertNotIn("option_extension", parsed["agreement_data"])

    def test_unicode_terms_are_preserved_on_continuation_pages(self):
        from lib.trec_39_11 import render_trec_39_11

        data = self.parsed()["agreement_data"]
        phrase = "Buyer’s café sign, résumé file, and 12½-inch fixture remain."
        data["other_modifications"] = " ".join([phrase] * 80)
        rendered = render_trec_39_11(SOURCE.read_bytes(), data)
        text = "\n".join((page.extract_text() or "") for page in PdfReader(BytesIO(rendered)).pages)
        self.assertIn("Buyer’s café sign", text)
        self.assertIn("12½-inch fixture", text)

    def test_recipient_preview_labels_buyers_then_sellers(self):
        agreement = {
            "form_code": "TREC-39-11",
            "client_names": ["Buyer One", "Seller One"],
            "agreement_data": {"buyer_names": ["Buyer One"], "seller_names": ["Seller One"]},
        }
        recipients = ADMIN._txr_signwell_recipients(
            agreement, ["buyer@example.com", "seller@example.com"], {}, {}
        )
        self.assertEqual([item["id"] for item in recipients], ["1", "2"])
        self.assertEqual(ADMIN._standalone_signer_labels(agreement), ["Buyer 1", "Seller 1"])
        self.assertIsNone(ADMIN._standalone_professional_role(agreement))

    def test_long_terms_continue_without_losing_any_party_initials(self):
        from lib.trec_39_11 import build_signwell_fields_trec3911, render_trec_39_11

        data = self.parsed()["agreement_data"]
        data["other_modifications"] = " ".join(["Exact entered amendment term"] * 180)
        rendered = render_trec_39_11(SOURCE.read_bytes(), data)
        self.assertGreater(len(PdfReader(BytesIO(rendered)).pages), 1)
        initials = [field for field in build_signwell_fields_trec3911(data)[0] if field["type"] == "initials"]
        self.assertEqual({field["recipient_id"] for field in initials}, {"1", "2", "3", "4"})

    def test_ui_source_gate_and_offline_shell_include_the_amendment(self):
        asset = (ROOT / "assets" / "trec-39-11-amendment.js").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        uploader = (ROOT / "lib" / "platform_form_source_upload.py").read_text(encoding="utf-8")
        migration = (ROOT / "supabase" / "migrations" / "20261005110000_expand_trec_39_11_source_code.sql").read_text(encoding="utf-8")
        self.assertIn('name="propertyAddress"', asset)
        self.assertIn('autocomplete="street-address"', asset)
        self.assertIn("What needs to change?", asset)
        self.assertIn("Amend an existing contract", html)
        self.assertIn("'/assets/trec-39-11-amendment.js'", worker)
        self.assertIn('"TREC-39-11"', uploader)
        self.assertIn("'TREC-39-11'", migration)


if __name__ == "__main__":
    unittest.main()
