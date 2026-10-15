import asyncio
from io import BytesIO
import importlib.util
from pathlib import Path
import unicodedata
import unittest
from unittest.mock import AsyncMock, patch

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from lib import trec_seller_disclosure as disclosure
from lib import seller_disclosure_explanations as details
from lib.seller_disclosure_draft import parse_seller_disclosure_draft

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("disclosure_explanation_admin", ROOT / "api/admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
USER = {"id": "11111111-1111-4111-8111-111111111111"}
DRAFT_ID = "22222222-2222-4222-8222-222222222222"


def blank_pdf(pages):
    output = BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(pages):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


class SellerDisclosureExplanationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main_source, cls.water_source = blank_pdf(4), blank_pdf(2)

    def render(self, code, values, **kwargs):
        with patch.object(disclosure, "validate_source_bytes"):
            return disclosure.render_unsigned_preview(
                self.main_source if code == "TREC-55-1" else self.water_source,
                code, values, qa_mode=True, **kwargs)

    def test_every_named_explanation_survives_the_real_renderer(self):
        for code, entries in details.DETAILS.items():
            for index, (key, _, _, _) in enumerate(entries):
                with self.subTest(form=code, key=key):
                    value = f"Fictional explanation {index}: review the documented issue."
                    reader = PdfReader(BytesIO(self.render(code, {key: value})))
                    self.assertIn(value, normalized(" ".join(page.extract_text() for page in reader.pages)))

    def test_long_unicode_and_literal_markup_are_not_cut_off(self):
        value = ("Élodie reviewed the façade. 张伟 confirmed café <paint> & trim. " * 35).strip()
        reader = PdfReader(BytesIO(self.render("TREC-55-1", {"conditions_explanation": value})))
        self.assertGreater(len(reader.pages), 4)
        self.assertIn(details.REFERENCE, reader.pages[1].extract_text())
        self.assertIn(normalized(value), normalized(" ".join(page.extract_text() for page in reader.pages[4:])))

    def test_long_unbroken_word_is_moved_to_continuation_without_truncation(self):
        value = "X" * 1800
        reader = PdfReader(BytesIO(self.render("TREC-55-1", {"known_defects_explanation": value})))
        note_text = "".join(page.extract_text().replace("\n", "") for page in reader.pages[4:])
        self.assertIn(value, note_text)

    def test_legacy_and_extra_notes_remain_literal(self):
        reader = PdfReader(BytesIO(self.render("TREC-55-1", {
            "repairs_flood_explanation": "Original combined repairs/flood answer.",
            "notes_external": "An older saved note with <literal> punctuation.",
        })))
        text = " ".join(page.extract_text() for page in reader.pages)
        self.assertIn("Original combined repairs/flood answer.", text)
        self.assertIn("<literal>", text)
        self.assertNotIn("notes_external", text)

    def test_no_added_pages_or_fields_for_empty_explanations(self):
        reader = PdfReader(BytesIO(self.render("TREC-55-1", {"conditions_explanation": ""})))
        self.assertEqual(len(reader.pages), 4)
        self.assertEqual(details.continuation_fields({"seller_names": ["QA"]}, []), [])

    def test_multiple_continuation_pages_repeat_context_without_losing_sections(self):
        values = {key: ("Fictional detailed seller explanation for this section. " * 45).strip()
                  for key, _, _, blanks in details.DETAILS["TREC-55-1"] if blanks}
        reader = PdfReader(BytesIO(self.render("TREC-55-1", {**values, "propertyAddress": "100 Fictional QA Lane"},
                                              parties={"seller_names": ["QA Seller"], "buyer_names": []})))
        self.assertGreater(len(reader.pages), 5)
        for page in reader.pages[4:]:
            self.assertIn("100 Fictional QA Lane", page.extract_text())
            self.assertIn("Seller 1 initials", page.extract_text())
            self.assertNotIn("Purchaser 1 initials", page.extract_text())
        all_notes = normalized(" ".join(page.extract_text() for page in reader.pages[4:]))
        for key, label, _, blanks in details.DETAILS["TREC-55-1"]:
            if blanks:
                self.assertIn(label, all_notes)

    def test_draft_validation_preserves_answers_without_attesting(self):
        text = "Line one: café.\nLine two: <paint> & trim."
        data = {"formCode": "TREC-55-1", "disclosureSourceId": DRAFT_ID,
                "propertyAddress": "100 Fictional QA Lane", "sellerNames": ["QA Seller"],
                "responseData": {"repair_explanation": text}}
        parsed = parse_seller_disclosure_draft(data)
        self.assertEqual(parsed["response_data"]["repair_explanation"], text)
        self.assertFalse(parsed["seller_review_attested"])
        for bad in (True, {"nested": "text"}, "X" * 3001, "invalid\x00text"):
            with self.subTest(bad=type(bad).__name__), self.assertRaises(ValueError):
                parse_seller_disclosure_draft({**data, "responseData": {"repair_explanation": bad}})

    def test_continuation_initials_match_each_actual_seller_and_receiving_buyer(self):
        for sellers in (1, 2):
            for buyers in (0, 1, 2):
                with self.subTest(sellers=sellers, buyers=buyers):
                    data = {"seller_names": ["QA"] * sellers, "buyer_names": ["QA"] * buyers}
                    fields = details.continuation_fields(data, [7, 8])
                    self.assertEqual(len(fields), (sellers + buyers) * 2)
                    self.assertEqual(len({f["api_id"] for f in fields}), len(fields))
                    for page in (7, 8):
                        self.assertEqual({f["recipient_id"] for f in fields if f["page"] == page},
                                         {str(i + 1) for i in range(sellers + buyers)})
                    for field in fields:
                        self.assertLessEqual(field["x"] + field["width"], 816)
                        self.assertLess(field["y"] + field["height"], (792 - 63) * 4 / 3)

    def test_actual_send_keeps_water_on_pages_five_six_and_one_field_group(self):
        record = {"id": DRAFT_ID, "brokerage_id": "fictional-library", "property_address": "100 Fictional QA Lane",
                  "seller_names": ["QA Seller One", "QA Seller Two"], "buyer_names": ["QA Buyer"],
                  "disclosure_source_id": "main-source", "water_source_id": "water-source",
                  "disclosure_source_revision": "qa-revision", "water_source_revision": "qa-revision",
                  "response_data": {"conditions_explanation": "QA explanation of the condition. " * 65},
                  "water_rights_data": {"well_agreement": "QA shared-well agreement details. " * 50}}
        async def get(path):
            if path.startswith("hof_seller_disclosure_drafts?"):
                return [record]
            water = "TREC-61-0" in path
            return [{"id": "water-source" if water else "main-source", "source_revision": "qa-revision",
                     "storage_bucket": "fictional", "storage_path": "water" if water else "main"}]
        sources = self
        class Client:
            def __init__(self, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def get(self, url, **kwargs):
                class Response: pass
                response = Response(); response.status_code = 200
                response.content = sources.water_source if url.endswith("water") else sources.main_source
                return response
        deliver = AsyncMock(return_value={"document_id": "fictional", "document": {"status": "sent"},
                                         "message": "fictional only", "recovered": False})
        with patch.multiple(API, TXR_SIGNING_ENABLED=True, SIGNWELL_ENABLED=True,
                            SIGNWELL_API_KEY="fictional", SIGNWELL_TEST_MODE=True), \
             patch.object(API, "_get", get), patch.object(API.httpx, "AsyncClient", Client), \
             patch.object(API, "_deliver_tracked_signwell_request", deliver), \
             patch.object(disclosure, "validate_source_bytes"):
            result = asyncio.run(API._send_seller_disclosure_for_signature(USER, {
                "draftId": DRAFT_ID, "signerEmails": ["qa-one@example.com", "qa-two@example.com", "qa-three@example.com"]}))
        self.assertEqual(result["recipientCount"], 3)
        payload = deliver.await_args.args[5]
        import base64
        reader = PdfReader(BytesIO(base64.b64decode(payload["files"][0]["file_base64"])))
        self.assertGreater(len(reader.pages), 6)
        self.assertEqual(len(payload["fields"]), len(payload["files"]))
        fields = payload["fields"][0]
        self.assertEqual({f["page"] for f in fields if f["api_id"].startswith("trec551")}, {4})
        self.assertEqual({f["page"] for f in fields if f["api_id"].startswith("trec610")}, {6})
        for page in range(7, len(reader.pages) + 1):
            self.assertEqual({f["recipient_id"] for f in fields if f["page"] == page}, {"1", "2", "3"})
        self.assertFalse(payload["apply_signing_order"])
        context = deliver.await_args.args[6]
        self.assertEqual(context["render_context"]["render_revision"], details.RENDER_REVISION)
