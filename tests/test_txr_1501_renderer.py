import io
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib import txr_1501
from lib.txr_1501 import build_signwell_fields_txr1501, render_txr_1501


def blank_six_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(6):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "client_names": ["Test Buyer One", "Test Buyer Two"],
        "client_address": "721 Broderick Lane",
        "client_city_state_zip": "Prosper, TX 75078",
        "client_phone": "2143649890",
        "client_email": "buyer@example.com",
        "market_area": "Collin and Denton Counties, Texas",
        "term_start": "2026-08-01",
        "term_end": "2027-01-31",
        "compensation": {"purchase_percentage": "3"},
        "retainer_amount": "",
        "retainer_treatment": "",
        "protection_days": "30",
        "payment_county": "Collin",
        "intermediary": "authorized",
        "signer_plan": "clients_and_associate",
    }


class Txr1501RendererTests(unittest.TestCase):
    def test_retainer_checkbox_marks_use_the_printed_source_cells(self):
        brokerage = {"legal_name": "OnDemand Realty", "license_number": "9010832"}
        associate = {"name": "Andrew Christian", "license_number": "0738821"}
        with patch.object(txr_1501, "_check") as draw_check:
            txr_1501._overlay(
                {**sample_data(), "retainer_amount": "100", "retainer_treatment": "apply"},
                brokerage,
                associate,
            )
        self.assertIn((262, 414), [call.args[1:] for call in draw_check.call_args_list])

        with patch.object(txr_1501, "_check") as draw_check:
            txr_1501._overlay(
                {**sample_data(), "retainer_amount": "100", "retainer_treatment": "not_apply"},
                brokerage,
                associate,
            )
        self.assertIn((320, 414), [call.args[1:] for call in draw_check.call_args_list])

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
        txr_1501._check(canvas, 100, 200)

        self.assertEqual(canvas.line_width, 1.3)
        self.assertEqual(len(canvas.lines), 2)
        for x1, y1, x2, y2 in canvas.lines:
            for x in (x1, x2):
                self.assertGreaterEqual(x, 100)
                self.assertLessEqual(x, 108)
            for y in (y1, y2):
                self.assertGreaterEqual(y, 200)
                self.assertLessEqual(y, 207)

    def test_selected_signing_role_is_marked_in_the_source_checkbox(self):
        brokerage = {"legal_name": "OnDemand Realty", "license_number": "9010832"}
        associate = {"name": "Andrew Christian", "license_number": "0738821"}
        with patch.object(txr_1501, "_check_signing_role") as draw_check:
            txr_1501._overlay(sample_data(), brokerage, associate)
        self.assertIn((33, 329), [call.args[1:] for call in draw_check.call_args_list])

        with patch.object(txr_1501, "_check_signing_role") as draw_check:
            txr_1501._overlay(
                {**sample_data(), "signer_plan": "clients_and_broker"},
                brokerage,
                associate,
            )
        self.assertIn((33, 341), [call.args[1:] for call in draw_check.call_args_list])

    def test_completion_values_begin_on_the_released_source_rules(self):
        """Prevent a completed TXR-1501 from drifting into its labels.

        These coordinates are based on the released private source and the
        completed-packet review.  A text-presence test alone cannot catch a
        value that is visibly centered in the wrong blank.
        """
        brokerage = {
            "legal_name": "OnDemand Realty",
            "license_number": "9010832",
            "address": "12225 Greenville Ave",
            "city_state_zip": "Dallas, TX 75243",
            "phone": "214-766-5833",
            "email": "broker@example.com",
        }
        associate = {"name": "Andrew Christian", "license_number": "0738821"}
        with patch.object(txr_1501, "_draw") as draw:
            txr_1501._overlay(sample_data(), brokerage, associate)
        calls = {(call.args[1], call.args[2], call.args[3]) for call in draw.call_args_list}
        expected = {
            ("Test Buyer One, Test Buyer Two", 108, 612),
            ("721 Broderick Lane", 128, 594),
            ("Prosper, TX 75078", 158, 578),
            ("2143649890", 117, 562),
            ("buyer@example.com", 115, 546),
            ("OnDemand Realty", 108, 531),
            ("2026-08-01", 224, 176),
            ("2027-01-31", 430, 176),
            ("OnDemand Realty", 36, 400),
            ("Test Buyer One", 324, 400),
            ("Andrew Christian", 36, 309),
            ("Test Buyer Two", 324, 309),
        }
        self.assertTrue(expected.issubset(calls))

    def test_renderer_preserves_six_pages_and_overlays_supplied_values(self):
        rendered = render_txr_1501(
            blank_six_page_pdf(),
            sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"name": "Andrew Christian", "license_number": "0738821"},
        )
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 6)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("Test Buyer One, Test Buyer Two", "OnDemand Realty", "Collin and Denton Counties, Texas", "2026-08-01", "2027-01-31", "9010832", "Andrew Christian"):
            self.assertIn(expected, text)

    def test_renderer_uses_authenticated_profile_agent_name(self):
        rendered = render_txr_1501(
            blank_six_page_pdf(), sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"agent_name": "Andrew Christian", "license_number": "0738821"},
        )
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(rendered)).pages)
        self.assertIn("Andrew Christian", text)

    def test_signer_map_requires_plan_and_supports_one_or_two_clients(self):
        one = build_signwell_fields_txr1501({**sample_data(), "signer_plan": "clients_and_associate"}, client_count=1)[0]
        two = build_signwell_fields_txr1501({**sample_data(), "signer_plan": "clients_and_associate"}, client_count=2)[0]
        self.assertEqual(len(one), 4)
        self.assertEqual(len(two), 6)
        self.assertTrue(all(field["page"] == 6 for field in two))
        self.assertEqual({field["api_id"] for field in one}, {"txr1501_client1_signature_p6", "txr1501_client1_date_p6", "txr1501_associate_signature_p6", "txr1501_associate_date_p6"})
        self.assertEqual(next(field["x"] for field in two if field["api_id"] == "txr1501_client1_signature_p6"), 432)
        self.assertEqual(next(field["y"] for field in two if field["api_id"] == "txr1501_client1_signature_p6"), 566)
        self.assertEqual(next(field["y"] for field in two if field["api_id"] == "txr1501_client2_signature_p6"), 677)
        self.assertEqual(next(field["y"] for field in two if field["api_id"] == "txr1501_associate_signature_p6"), 677)
        self.assertEqual(next(field["x"] for field in two if field["api_id"] == "txr1501_client1_date_p6"), 720)
        self.assertEqual(next(field["width"] for field in two if field["api_id"] == "txr1501_client1_date_p6"), 48)
        self.assertEqual(next(field["x"] for field in two if field["api_id"] == "txr1501_associate_date_p6"), 336)
        self.assertEqual(next(field["width"] for field in two if field["api_id"] == "txr1501_associate_date_p6"), 48)
        with self.assertRaisesRegex(ValueError, "broker or associate"):
            build_signwell_fields_txr1501({**sample_data(), "signer_plan": "clients_only"}, client_count=1)
        with self.assertRaisesRegex(ValueError, "broker or associate"):
            build_signwell_fields_txr1501({**sample_data(), "signer_plan": ""}, client_count=1)


if __name__ == "__main__":
    unittest.main()
