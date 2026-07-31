import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.txr_1506 import build_signwell_fields_txr1506, render_txr_1506


def blank_six_page_pdf():
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(6):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def sample_data():
    return {
        "client_names": ["Test Consumer One", "Test Consumer Two"],
        "additional_notice": "Bring any questions to the broker before signing.",
        "signer_plan": "consumers_and_associate",
    }


class Txr1506RendererTests(unittest.TestCase):
    def test_renderer_preserves_six_pages_and_overlays_notice_values(self):
        rendered = render_txr_1506(
            blank_six_page_pdf(), sample_data(), {"legal_name": "OnDemand Realty"}
        )
        reader = PdfReader(io.BytesIO(rendered))
        self.assertEqual(len(reader.pages), 6)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("Test Consumer One", "Test Consumer Two", "Bring any questions", "OnDemand Realty"):
            self.assertIn(expected, text)

    def test_signer_map_supports_one_or_two_consumers_and_requires_plan(self):
        one = build_signwell_fields_txr1506({**sample_data(), "signer_plan": "consumers_and_associate"}, client_count=1)[0]
        two = build_signwell_fields_txr1506(sample_data(), client_count=2)[0]
        self.assertEqual(len(one), 9)
        self.assertEqual(len(two), 16)
        self.assertTrue(all(field["page"] in {1, 2, 3, 4, 5, 6} for field in two))
        with self.assertRaisesRegex(ValueError, "authorized broker"):
            build_signwell_fields_txr1506({**sample_data(), "signer_plan": ""}, client_count=1)
        with self.assertRaisesRegex(ValueError, "authorized broker"):
            build_signwell_fields_txr1506({**sample_data(), "signer_plan": "consumers_only"}, client_count=1)


if __name__ == "__main__":
    unittest.main()
