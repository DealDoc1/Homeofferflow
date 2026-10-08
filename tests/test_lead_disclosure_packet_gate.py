from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from pypdf import PdfReader

from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


def lead_upload():
    return {
        "name": "seller-lead-disclosure.pdf",
        "type": "lead_based_paint",
        "base64": one_page_pdf_base64(),
    }


class LeadDisclosurePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_pre_1978_offer_includes_blank_trec_56_0_without_a_completed_disclosure(self):
        offer = minimal_offer(
            yearBuilt="1972",
            leadBuiltBefore1978="yes",
            leadDisclosureStatus="request",
            buyer2="Second Buyer",
            buyer2Email="buyer2@example.com",
            agentEmail="agent@example.com",
        )
        captured = {}
        original_stamp_pdf = adapter.verified.stamp_pdf

        def capture_main_form(path, pages):
            if Path(path).name == "20-19_0.pdf":
                captured["pages"] = pages
            elif Path(path).name == "lead_based_paint_56-0.pdf":
                captured["lead_pages"] = pages
            return original_stamp_pdf(path, pages)

        with patch.object(adapter.verified, "stamp_pdf", side_effect=capture_main_form):
            packet = adapter.fill_and_merge_20_19(offer)

        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 13)
        self.assertIn("TREC NO. 56", reader.pages[-1].extract_text())
        self.assertIn("Seller has no actual knowledge", reader.pages[-1].extract_text())
        self.assertEqual(offer["leadBasedPaintAttached"], "yes")
        page_nine_entries = captured["pages"][8]
        self.assertTrue(any(entry[0] == 62 and entry[1] == 430 and entry[2] for entry in page_nine_entries))
        lead_entries = captured.get("lead_pages", {}).get(0, [])
        self.assertTrue(any(entry[0] == 205 and entry[1] == 679 for entry in lead_entries))
        self.assertFalse(any(entry[0] in {92} and entry[1] in {407, 389} and entry[2] for entry in lead_entries))
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        lead_fields = [field for field in fields if "lead_based_paint_addendum" in field["api_id"]]
        self.assertEqual({(field["api_id"], field["page"], field["recipient_id"]) for field in lead_fields}, {
            ("buyer1_lead_based_paint_addendum_signature", 13, "1"),
            ("buyer1_lead_based_paint_addendum_date", 13, "1"),
            ("buyer2_lead_based_paint_addendum_signature", 13, "2"),
            ("buyer2_lead_based_paint_addendum_date", 13, "2"),
            ("buyer_agent_lead_based_paint_addendum_signature", 13, "3"),
            ("buyer_agent_lead_based_paint_addendum_date", 13, "3"),
        })
        self.assertEqual(
            {(field["api_id"], field["x"], field["y"]) for field in lead_fields},
            {
                ("buyer1_lead_based_paint_addendum_signature", 76, 768),
                ("buyer1_lead_based_paint_addendum_date", 290, 768),
                ("buyer2_lead_based_paint_addendum_signature", 76, 827),
                ("buyer2_lead_based_paint_addendum_date", 290, 827),
                ("buyer_agent_lead_based_paint_addendum_signature", 76, 886),
                ("buyer_agent_lead_based_paint_addendum_date", 290, 886),
            },
        )

    def test_pre_1978_single_buyer_packet_has_only_one_buyer_and_agent_signing_fields(self):
        offer = minimal_offer(
            yearBuilt="1972",
            leadBuiltBefore1978="yes",
            leadDisclosureStatus="request",
            buyer2="",
            buyer2Email="",
            agentEmail="agent@example.com",
            address="456 Sample Ave",
            city="Austin",
            county="Travis",
            zip="78701",
        )
        packet = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 13)
        self.assertIn("TREC NO. 56", reader.pages[-1].extract_text())

        lead_fields = [
            field for field in adapter.build_signwell_fields_20_19(offer, packet)[0]
            if "lead_based_paint_addendum" in field["api_id"]
        ]
        self.assertEqual({field["recipient_id"] for field in lead_fields}, {"1", "3"})
        self.assertEqual({field["page"] for field in lead_fields}, {13})
        self.assertEqual(
            {(field["api_id"], field["x"], field["y"]) for field in lead_fields},
            {
                ("buyer1_lead_based_paint_addendum_signature", 76, 768),
                ("buyer1_lead_based_paint_addendum_date", 290, 768),
                ("buyer_agent_lead_based_paint_addendum_signature", 76, 886),
                ("buyer_agent_lead_based_paint_addendum_date", 290, 886),
            },
        )

    def test_completed_uploaded_disclosure_replaces_blank_source_exactly_once(self):
        offer = minimal_offer(
            yearBuilt="1972",
            leadBuiltBefore1978="yes",
            leadDisclosureStatus="request",
            uploadedDisclosureDocs=[lead_upload()],
        )
        adapter.validate_supported_offer(offer)
        packet = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 13)
        self.assertNotIn("TREC NO. 56-0", reader.pages[-1].extract_text() or "")
        self.assertEqual(offer["leadBasedPaintAttached"], "yes")

    def test_unknown_year_continues_with_blank_source_included(self):
        offer = minimal_offer(
            yearBuilt="",
            leadBuiltBefore1978="unknown",
            leadDisclosureStatus="unknown",
        )
        adapter.validate_supported_offer(offer)
        packet = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 13)
        self.assertIn("TREC NO. 56", reader.pages[-1].extract_text())

    def test_legacy_attachment_flag_includes_blank_form_without_stopping_generation(self):
        offer = minimal_offer(leadBasedPaintAttached="yes")
        adapter.validate_supported_offer(offer)
        packet = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 13)
        self.assertIn("TREC NO. 56", reader.pages[-1].extract_text())

    def test_newer_home_without_lead_selection_does_not_get_unneeded_form(self):
        offer = minimal_offer(yearBuilt="2005", leadBuiltBefore1978="no")
        packet = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 12)
        self.assertFalse(any("lead_based_paint_addendum" in field["api_id"] for field in adapter.build_signwell_fields_20_19(offer, packet)[0]))

    def test_customer_copy_makes_completed_upload_optional_and_never_stops_on_missing_document(self):
        self.assertIn("Attach a completed TREC Form 56-0 (optional)", HTML)
        self.assertIn("the blank TREC form will be included automatically", HTML)
        self.assertNotIn("validateLeadDisclosurePacket", HTML)
        self.assertNotIn("requireRadioSelection('leadDisclosureStatus'", HTML)
        self.assertNotIn("Required before sending", HTML)


if __name__ == "__main__":
    unittest.main()
