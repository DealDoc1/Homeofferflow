from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from pypdf import PdfReader

from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_base64


def lead_upload():
    return {
        "name": "seller-lead-disclosure.pdf",
        "type": "lead_based_paint",
        "base64": one_page_pdf_base64(),
    }


class LeadDisclosurePacketGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_pre_1978_offer_includes_uploaded_disclosure_once(self):
        offer = minimal_offer(
            yearBuilt="1972",
            leadBuiltBefore1978="yes",
            leadDisclosureStatus="received",
            uploadedDisclosureDocs=[lead_upload()],
        )

        captured = {}
        original_stamp_pdf = adapter.verified.stamp_pdf

        def capture_main_form(path, pages):
            if Path(path).name == "20-19_0.pdf":
                captured["pages"] = pages
            return original_stamp_pdf(path, pages)

        with patch.object(adapter.verified, "stamp_pdf", side_effect=capture_main_form):
            packet = adapter.fill_and_merge_20_19(offer)

        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 13)
        self.assertEqual(offer["leadBasedPaintAttached"], "yes")
        page_nine_entries = captured["pages"][8]
        self.assertTrue(any(entry[0] == 62 and entry[1] == 430 and entry[2] for entry in page_nine_entries))
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        self.assertFalse(any("lead_based_paint_addendum" in field["api_id"] for field in fields))

    def test_pre_1978_offer_cannot_omit_actual_disclosure(self):
        with self.assertRaises(adapter.UnsupportedOfferPathError) as context:
            adapter.validate_supported_offer(minimal_offer(
                yearBuilt="1972",
                leadBuiltBefore1978="yes",
                leadDisclosureStatus="received",
            ))
        self.assertIn("uploaded lead-based paint disclosure PDF", str(context.exception))

    def test_pre_1978_offer_requires_received_status(self):
        with self.assertRaises(adapter.UnsupportedOfferPathError) as context:
            adapter.validate_supported_offer(minimal_offer(
                yearBuilt="1972",
                leadBuiltBefore1978="yes",
                leadDisclosureStatus="request",
                uploadedDisclosureDocs=[lead_upload()],
            ))
        self.assertIn("completed lead-based paint disclosure", str(context.exception))

    def test_unknown_year_cannot_reach_packet_generation(self):
        with self.assertRaises(adapter.UnsupportedOfferPathError) as context:
            adapter.validate_supported_offer(minimal_offer(
                yearBuilt="",
                leadBuiltBefore1978="unknown",
                leadDisclosureStatus="unknown",
            ))
        self.assertIn("confirm whether the home was built before 1978", str(context.exception))

    def test_legacy_blank_lead_form_flag_stays_blocked(self):
        with self.assertRaises(adapter.UnsupportedOfferPathError) as context:
            adapter.validate_supported_offer(minimal_offer(leadBasedPaintAttached="yes"))
        self.assertIn("instead of a generated blank form", str(context.exception))


if __name__ == "__main__":
    unittest.main()
