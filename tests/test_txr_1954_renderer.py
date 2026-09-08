import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1954 import build_signwell_fields_txr1954, render_txr_1954


def blank_one_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage(); canvas.save()
    return output.getvalue()


class Txr1954RendererTests(unittest.TestCase):
    def test_renderer_overlays_selected_values_and_preserves_long_notice(self):
        rendered = render_txr_1954(blank_one_page_pdf(), {
            "property_address": "1438 Whitaker Road, Van Alstyne, TX",
            "buyer_names": ["Buyer One", "Buyer Two"],
            "seller_names": ["Seller One", "Seller Two"],
            "leased_fixture_types": ["solar_panels", "other"],
            "leased_fixtures_other": "Pool equipment",
            "assumed_fixture_leases": ["solar_panels"],
            "buyer_first_cost": "2500",
            "removal_choice": "will_not",
            "delivery_choice": "oral_notice",
            "oral_fixture_lease_notice": "Solar lease with monthly payment and remaining term.",
        })
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("1438 Whitaker", "Buyer One", "Buyer Two", "Seller One", "Seller Two", "2500", "Pool equipment", "Solar lease"):
            self.assertIn(expected, text)

    def test_renderer_rejects_a_non_matching_source_length(self):
        output = io.BytesIO(); canvas = Canvas(output, pagesize=(612, 792)); canvas.showPage(); canvas.showPage(); canvas.save()
        with self.assertRaisesRegex(ValueError, "exactly one page"):
            render_txr_1954(output.getvalue(), {})

    def test_signer_map_covers_each_named_buyer_and_seller(self):
        fields = build_signwell_fields_txr1954({
            "buyer_names": ["Buyer One"],
            "seller_names": ["Seller One", "Seller Two"],
        })[0]
        self.assertEqual([field["recipient_id"] for field in fields], ["1", "2", "3"])
        self.assertTrue(all(field["type"] == "signature" for field in fields))
        self.assertEqual(len({field["api_id"] for field in fields}), 3)

    def test_signing_render_leaves_signature_lines_clear(self):
        rendered = render_txr_1954(blank_one_page_pdf(), {
            "buyer_names": ["Buyer One"],
            "seller_names": ["Seller One"],
            "_for_signing": True,
        })
        extracted = PdfReader(io.BytesIO(rendered)).pages[0].extract_text()
        self.assertNotIn("Buyer One", extracted)
        self.assertNotIn("Seller One", extracted)

    def test_long_fixture_notice_is_preserved_on_a_continuation_exhibit(self):
        notice = "Generator lease with monthly payment and eighteen months remaining."
        rendered = render_txr_1954(blank_one_page_pdf(), {
            "property_address": "1 Main Street, Sherman, TX 75090",
            "delivery_choice": "oral_notice",
            "oral_fixture_lease_notice": notice,
        })
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("TXR-1954 CONTINUATION EXHIBIT", text)
        self.assertIn(notice, text)


if __name__ == "__main__":
    unittest.main()
