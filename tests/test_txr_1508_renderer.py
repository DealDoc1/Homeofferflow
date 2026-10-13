import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib import txr_1508
from lib.txr_1508 import build_signwell_fields_txr1508, render_txr_1508


def blank_one_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "property_address": "1438 Whitaker Road, Van Alstyne, TX",
        "client_names": ["Test Customer One", "Test Customer Two"],
        "other_broker_agreement": ["no", "yes"],
        "signer_plan": "associate_and_clients",
    }


class Txr1508RendererTests(unittest.TestCase):
    def test_checkbox_mark_stays_within_the_small_source_cell(self):
        class RecordingCanvas:
            def __init__(self):
                self.line_width = None
                self.lines = []

            def setLineWidth(self, width):
                self.line_width = width

            def line(self, x1, y1, x2, y2):
                self.lines.append((x1, y1, x2, y2))

        canvas = RecordingCanvas()
        txr_1508._check(canvas, 100, 200)

        self.assertEqual(canvas.line_width, 1.3)
        self.assertEqual(len(canvas.lines), 2)
        for x1, y1, x2, y2 in canvas.lines:
            for x in (x1, x2):
                self.assertGreaterEqual(x, 100)
                self.assertLessEqual(x, 108)
            for y in (y1, y2):
                self.assertGreaterEqual(y, 200)
                self.assertLessEqual(y, 207)

    def test_renderer_preserves_one_page_and_overlays_scope_limited_values(self):
        rendered = render_txr_1508(
            blank_one_page_pdf(), sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"name": "Andrew Christian", "license_number": "0738821"},
        )
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 1)
        text = reader.pages[0].extract_text() or ""
        for expected in ("1438 Whitaker Road, Van Alstyne, TX", "Test Customer One", "Test Customer Two", "OnDemand Realty", "Andrew Christian"):
            self.assertIn(expected, text)

    def test_renderer_uses_authenticated_profile_agent_name(self):
        rendered = render_txr_1508(
            blank_one_page_pdf(), sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"agent_name": "Andrew Christian", "license_number": "0738821"},
        )
        text = PdfReader(io.BytesIO(rendered)).pages[0].extract_text() or ""
        self.assertIn("Andrew Christian", text)

    def test_signer_map_is_explicit_for_one_or_two_customers(self):
        one = build_signwell_fields_txr1508({**sample_data(), "signer_plan": "broker_and_clients"}, client_count=1)[0]
        two = build_signwell_fields_txr1508(sample_data(), client_count=2)[0]
        self.assertEqual(len(one), 4)
        self.assertEqual(len(two), 6)
        self.assertTrue(all(field["page"] == 1 for field in two))
        self.assertEqual(next(field["x"] for field in two if field["api_id"] == "txr1508_agent_initials_p1"), 347)
        self.assertEqual(next(field["width"] for field in two if field["api_id"] == "txr1508_agent_initials_p1"), 95)
        self.assertEqual(next(field["x"] for field in two if field["api_id"] == "txr1508_client1_initials_p1"), 518)
        self.assertEqual(next(field["width"] for field in two if field["api_id"] == "txr1508_client1_initials_p1"), 61)
        for field_id in ("txr1508_agent_date_p1", "txr1508_client1_date_p1", "txr1508_client2_date_p1"):
            field = next(field for field in two if field["api_id"] == field_id)
            self.assertEqual((field["x"], field["width"]), (625, 121))
        self.assertEqual(next(field["y"] for field in two if field["api_id"] == "txr1508_client2_initials_p1"), 794)
        with self.assertRaisesRegex(ValueError, "broker or associate"):
            build_signwell_fields_txr1508({**sample_data(), "signer_plan": ""}, client_count=1)


if __name__ == "__main__":
    unittest.main()
