import importlib.util
from io import BytesIO
from pathlib import Path
import unittest

from pypdf import PdfReader
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("txr_1507_renderer", ROOT / "api" / "txr_1507_renderer.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def source_fixture():
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=(612, 792))
    c.drawString(36, 760, "TXR-1507 source fixture")
    c.showPage()
    c.drawString(36, 760, "TXR-1507 source fixture page 2")
    c.save()
    return output.getvalue()


def valid_data():
    return {
        "client_names": ["Buyer One", "Buyer Two"],
        "market_area": "Collin County, Texas",
        "term_start": "2026-08-01",
        "term_end": "2027-01-31",
        "service_level": "full_services",
        "purchase_percentage": "3",
        "intermediary": "authorized",
    }


class TXR1507RendererTests(unittest.TestCase):
    def test_renderer_requires_private_approved_source(self):
        with self.assertRaisesRegex(MODULE.TXR1507RenderError, "source PDF"):
            MODULE.render_txr_1507_draft(b"not-a-pdf", "TXR-1507 06-15-26", valid_data(), {"name": "Broker"})

    def test_renderer_rejects_wrong_page_count(self):
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=(612, 792))
        c.drawString(36, 760, "one page")
        c.save()
        with self.assertRaisesRegex(MODULE.TXR1507RenderError, "exactly two pages"):
            MODULE.render_txr_1507_draft(output.getvalue(), "TXR-1507 06-15-26", valid_data(), {"name": "Broker"})

    def test_renderer_validates_required_intermediary_and_compensation(self):
        data = valid_data()
        data["intermediary"] = ""
        with self.assertRaisesRegex(MODULE.TXR1507RenderError, "intermediary"):
            MODULE.normalize_txr_1507_data(data)
        data = valid_data()
        data["purchase_percentage"] = ""
        with self.assertRaisesRegex(MODULE.TXR1507RenderError, "compensation"):
            MODULE.normalize_txr_1507_data(data)

    def test_renderer_produces_two_pages_and_preserves_client_data(self):
        packet = MODULE.render_txr_1507_draft(
            source_fixture(),
            "TXR-1507 06-15-26",
            valid_data(),
            {"name": "OnDemand Realty", "license": "9010832", "associate_name": "Andrew Christian", "associate_license": "0738821"},
        )
        reader = PdfReader(BytesIO(packet))
        self.assertEqual(len(reader.pages), 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Buyer One and Buyer Two", text)
        self.assertIn("OnDemand Realty", text)
        self.assertIn("Collin County, Texas", text)
        self.assertIn("08/01/2026", text)
        self.assertIn("01/31/2027", text)

    def test_renderer_accepts_full_lease_compensation_matrix(self):
        data = {
            "client_names": ["Tenant One", "Tenant Two"],
            "market_area": "Dallas and Collin Counties, Texas",
            "term_start": "2026-08-15",
            "term_end": "2027-08-14",
            "service_level": "full_services",
            "lease_one_month_percentage": "100",
            "lease_total_rents_percentage": "5",
            "lease_flat_fee": "750",
            "intermediary": "authorized",
        }
        normalized = MODULE.normalize_txr_1507_data(data)
        self.assertEqual(normalized["lease_one_month_percentage"], "100")
        self.assertEqual(normalized["lease_total_rents_percentage"], "5")
        self.assertEqual(normalized["lease_flat_fee"], "750")
        entries = MODULE.overlay_entries(data, {"name": "OnDemand Realty", "license": "9010832"})
        page_one_text = " ".join(entry[2] for entry in entries[0])
        self.assertIn("100", page_one_text)
        self.assertIn("5", page_one_text)
        self.assertIn("750", page_one_text)


if __name__ == "__main__":
    unittest.main()
