"""Unknown must never become Yes, No or a vanished answer in the actual PDF."""
from copy import deepcopy
from io import BytesIO
import unittest
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib import trec_seller_disclosure as forms
from lib.seller_disclosure_explanations import append_explanations, continuation_fields
from lib.seller_disclosure_draft import parse_seller_disclosure_draft


class SellerDisclosureUnknownPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {}
        for code, pages in (("TREC-55-1", 4), ("TREC-61-0", 2)):
            stream = BytesIO(); canvas = Canvas(stream, pagesize=(612, 792))
            for _ in range(pages):
                canvas.showPage()
            canvas.save(); cls.sources[code] = stream.getvalue()

    def render(self, code, values, **kwargs):
        with patch.object(forms, "validate_source_bytes"):
            return forms.render_unsigned_preview(self.sources[code], code, values,
                                                 qa_mode=True, **kwargs)

    def test_every_yes_no_only_unknown_is_retained_once_without_source_mark(self):
        for code, labels in forms.YES_NO_ONLY_RESPONSES.items():
            for key, label in labels.items():
                with self.subTest(form=code, key=key), patch.object(forms, "_check") as mark:
                    reader = PdfReader(BytesIO(self.render(code, {key: "U"})))
                    source_count = 4 if code == "TREC-55-1" else 2
                    self.assertEqual(len(reader.pages), source_count + 1)
                    mark.assert_not_called()
                    for page in reader.pages[:source_count]:
                        self.assertEqual(page.extract_text().strip(), "")
                    notes = " ".join(p.extract_text() for p in reader.pages[source_count:])
                    self.assertIn(label, notes)
                    self.assertEqual(notes.count("Seller's answer: Unknown."), 1)
                    self.assertIn("Yes/No answer on the form is blank.", notes)
                    self.assertNotIn(key, notes)

    def test_yes_and_no_stay_on_source_and_do_not_add_unknown_notes(self):
        for code, keys in forms.YES_NO_ONLY_RESPONSES.items():
            for value in (True, False, "Y", "N", "", None):
                reader = PdfReader(BytesIO(self.render(code, {key: value for key in keys})))
                self.assertEqual(len(reader.pages), 4 if code == "TREC-55-1" else 2)
                self.assertNotIn("Seller's answer: Unknown", " ".join(p.extract_text() for p in reader.pages))

    def test_real_unknown_source_choices_remain_on_the_original_page(self):
        for code, values, check_count in (
            ("TREC-55-1", {"range": "U", "water_heater_gas": "U",
                           "property_items_condition_issue": "U", "working_smoke_detectors": "U"}, 2),
            ("TREC-61-0", {"in_groundwater_district": "U"}, 1),
        ):
            with patch.object(forms, "_check", wraps=forms._check) as mark:
                reader = PdfReader(BytesIO(self.render(code, values)))
                self.assertEqual(mark.call_count, check_count)
            self.assertEqual(len(reader.pages), 4 if code == "TREC-55-1" else 2)

    def test_original_data_and_older_unknown_spellings_are_retained(self):
        for value in ("U", "u", "Unknown", " unknown "):
            data = {"seller_occupancy": value, "seller_occupancy_yes": True,
                    "known_defects_explanation": "Original seller facts.",
                    "_delivery_checkpoint": {"id": "test-only"}}
            original = deepcopy(data)
            with patch.object(forms, "_check") as mark:
                reader = PdfReader(BytesIO(self.render("TREC-55-1", data)))
                mark.assert_not_called()
            self.assertEqual(data, original)
            self.assertIn("Seller's answer: Unknown", reader.pages[-1].extract_text())
            self.assertIn("Original seller facts.", reader.pages[1].extract_text())

    def test_combined_packet_keeps_water_pages_and_initials_for_all_actual_parties(self):
        for sellers in (1, 2):
            for buyers in (0, 1, 2):
                parties = {"seller_names": ["QA Seller"] * sellers, "buyer_names": ["QA Buyer"] * buyers}
                notes, writer = [], PdfWriter()
                for code, values in (("TREC-55-1", {"defect_roof": "U"}),
                                     ("TREC-61-0", {"water_wells_known": "U"})):
                    rendered = self.render(code, values, continuation_sink=notes)
                    for page in PdfReader(BytesIO(rendered)).pages:
                        writer.add_page(page)
                stream = BytesIO(); writer.write(stream)
                packet, pages = append_explanations(stream.getvalue(), notes,
                    property_address="100 Fictional QA Lane", parties=parties)
                self.assertEqual(pages, [7])
                text = PdfReader(BytesIO(packet)).pages[6].extract_text()
                self.assertIn("Section 3 - Known defects: roof", text)
                self.assertIn("Section 2B - Awareness of water wells", text)
                fields = continuation_fields(parties, pages)
                self.assertEqual({f["recipient_id"] for f in fields}, {str(i+1) for i in range(sellers+buyers)})
                self.assertEqual({f["page"] for f in fields}, {7})
                self.assertTrue(all(f["required"] for f in fields))

    def test_saved_draft_keeps_unknowns_without_attesting_to_them(self):
        data = {"formCode": "TREC-55-1", "disclosureSourceId": "11111111-1111-4111-8111-111111111111",
                "propertyAddress": "100 Fictional QA Lane", "sellerNames": ["QA Seller"],
                "responseData": {"defect_roof": "U", "filed_flood_claim": "U"},
                "waterRightsData": {"water_wells_known": "U"}}
        draft = parse_seller_disclosure_draft(data)
        self.assertEqual(draft["response_data"], data["responseData"])
        self.assertEqual(draft["water_rights_data"], data["waterRightsData"])
        self.assertFalse(draft["seller_review_attested"])
