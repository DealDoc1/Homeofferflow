import io
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib import txr_1507
from lib.txr_1507 import build_signwell_fields_txr1507, render_txr_1507


def blank_two_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    canvas.showPage()
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "client_names": ["Test Buyer One", "Test Buyer Two"],
        "market_area": "1438 Whitaker Road, Van Alstyne, Grayson County, Texas 75495",
        "term_start": "2026-08-01",
        "term_end": "2027-01-31",
        "service_level": "full_services",
        "showing_fee": "",
        "compensation": {
            "purchase_percentage": "3",
            "purchase_flat_fee": "",
            "lease_one_month_percentage": "",
            "lease_total_rents_percentage": "",
            "lease_flat_fee": "",
        },
        "intermediary": "authorized",
        "signer_plan": "clients_and_associate",
    }


class Txr1507RendererTests(unittest.TestCase):
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
        txr_1507._draw_check(canvas, 100, 200)

        self.assertEqual(canvas.line_width, 1.0)
        self.assertEqual(len(canvas.lines), 2)
        for x1, y1, x2, y2 in canvas.lines:
            for x in (x1, x2):
                self.assertGreaterEqual(x, 100)
                self.assertLessEqual(x, 108)
            for y in (y1, y2):
                self.assertGreaterEqual(y, 200)
                self.assertLessEqual(y, 207)

    def test_full_services_mark_uses_the_current_source_checkbox(self):
        """Keep the 06-15-26 Full Services selection inside its printed box."""
        with patch.object(txr_1507, "_draw_check") as draw_check:
            txr_1507._overlay(
                sample_data(),
                {"legal_name": "OnDemand Realty", "license_number": "9010832"},
                {"name": "Andrew Christian", "license_number": "0738821"},
            )
        self.assertIn((56, 461), [call.args[1:] for call in draw_check.call_args_list])

    def test_selected_signing_role_is_marked_in_the_source_checkbox(self):
        with patch.object(txr_1507, "_draw_signing_role_check") as draw_check:
            txr_1507._overlay(
                sample_data(),
                {"legal_name": "OnDemand Realty", "license_number": "9010832"},
                {"name": "Andrew Christian", "license_number": "0738821"},
            )
        self.assertIn((37, 242), [call.args[1:] for call in draw_check.call_args_list])

        with patch.object(txr_1507, "_draw_signing_role_check") as draw_check:
            txr_1507._overlay(
                {**sample_data(), "signer_plan": "clients_and_broker"},
                {"legal_name": "OnDemand Realty", "license_number": "9010832"},
                {"name": "Andrew Christian", "license_number": "0738821"},
            )
        self.assertIn((37, 254), [call.args[1:] for call in draw_check.call_args_list])

    def test_renderer_preserves_two_pages_and_overlays_only_supplied_values(self):
        rendered = render_txr_1507(
            blank_two_page_pdf(),
            sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"name": "Andrew Christian", "license_number": "0738821"},
        )
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("Test Buyer One, Test Buyer Two", "OnDemand Realty", "1438 Whitaker Road", "2026-08-01", "2027-01-31", "9010832", "Andrew Christian"):
            self.assertIn(expected, text)

    def test_renderer_uses_authenticated_profile_agent_name(self):
        rendered = render_txr_1507(
            blank_two_page_pdf(), sample_data(),
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"agent_name": "Andrew Christian", "license_number": "0738821"},
        )
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(rendered)).pages)
        self.assertIn("Andrew Christian", text)

    def test_renderer_covers_showing_services_and_lease_compensation_path(self):
        data = sample_data()
        data.update({
            "service_level": "showing_services",
            "showing_fee": "150",
            "intermediary": "not_authorized",
            "compensation": {
                "purchase_percentage": "",
                "purchase_flat_fee": "",
                "lease_one_month_percentage": "50",
                "lease_total_rents_percentage": "10",
                "lease_flat_fee": "250",
            },
        })
        rendered = render_txr_1507(
            blank_two_page_pdf(),
            data,
            {"legal_name": "OnDemand Realty", "license_number": "9010832"},
            {"name": "Andrew Christian", "license_number": "0738821"},
        )
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(rendered)).pages)
        for expected in ("150", "50", "10", "250"):
            self.assertIn(expected, text)

    def test_signer_map_is_separate_for_one_and_two_clients(self):
        one = build_signwell_fields_txr1507(sample_data(), client_count=1)[0]
        two = build_signwell_fields_txr1507(sample_data(), client_count=2)[0]
        self.assertEqual(len(one), 6)
        self.assertEqual(len(two), 9)
        self.assertTrue(all(field["page"] in {1, 2} for field in two))
        self.assertTrue(all(field["recipient_id"] in {"1", "2", "associate"} for field in two))
        self.assertEqual(next(field["y"] for field in two if field["api_id"] == "txr1507_associate_signature_p2"), 634)
        self.assertEqual(next(field["y"] for field in two if field["api_id"] == "txr1507_client2_signature_p2"), 753)
        self.assertEqual(next(field["x"] for field in two if field["api_id"] == "txr1507_client1_signature_p2"), 350)
        initials = {field["api_id"]: field for field in two}
        # Keep the completed-packet calibration intact.  SignWell's rendered
        # values sit right and below the nominal widgets, so these top-origin
        # coordinates keep every visible value on its source rule.
        self.assertEqual(
            (initials["txr1507_client1_signature_p2"]["x"], initials["txr1507_client1_signature_p2"]["y"], initials["txr1507_client1_date_p2"]["x"], initials["txr1507_client1_date_p2"]["y"]),
            (350, 654, 455, 654),
        )
        self.assertEqual(
            (initials["txr1507_client2_signature_p2"]["x"], initials["txr1507_client2_signature_p2"]["y"], initials["txr1507_client2_date_p2"]["x"], initials["txr1507_client2_date_p2"]["y"]),
            (350, 753, 455, 753),
        )
        self.assertEqual(
            (initials["txr1507_associate_signature_p2"]["x"], initials["txr1507_associate_signature_p2"]["y"], initials["txr1507_associate_date_p2"]["x"], initials["txr1507_associate_date_p2"]["y"]),
            (10, 634, 115, 634),
        )
        # TXR-1507's footer has a separate Broker/Associate initial blank
        # before the two Client blanks. Every party named in that footer must
        # receive its own correctly aligned required field.
        self.assertEqual(
            (initials["txr1507_associate_initials_p1"]["x"], initials["txr1507_associate_initials_p1"]["y"], initials["txr1507_associate_initials_p1"]["width"]),
            (435, 984, 47),
        )
        self.assertEqual(
            (initials["txr1507_client1_initials_p1"]["x"], initials["txr1507_client1_initials_p1"]["y"], initials["txr1507_client1_initials_p1"]["width"]),
            (542, 984, 47),
        )
        self.assertEqual(
            (initials["txr1507_client2_initials_p1"]["x"], initials["txr1507_client2_initials_p1"]["y"], initials["txr1507_client2_initials_p1"]["width"]),
            (596, 984, 47),
        )
        self.assertEqual({field["api_id"] for field in one}, {
            "txr1507_associate_initials_p1",
            "txr1507_client1_initials_p1",
            "txr1507_client1_signature_p2",
            "txr1507_client1_date_p2",
            "txr1507_associate_signature_p2",
            "txr1507_associate_date_p2",
        })
        with self.assertRaisesRegex(ValueError, "authorized broker"):
            build_signwell_fields_txr1507({**sample_data(), "signer_plan": "clients_only"}, client_count=1)


if __name__ == "__main__":
    unittest.main()
