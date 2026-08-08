import tempfile
import unittest
import shutil
from pathlib import Path

from pypdf import PdfWriter

from scripts.render_qa_pdf import render


class RenderQaPdfTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("pdftoppm"), "pdftoppm is not installed in this test environment")
    def test_render_is_page_count_guarded_and_metadata_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "preview.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            writer.add_blank_page(width=612, height=792)
            with pdf.open("wb") as stream:
                writer.write(stream)
            result = render(pdf, root / "rendered", dpi=72)
            self.assertTrue(result["ok"])
            self.assertEqual(result["input_page_count"], 2)
            self.assertEqual(len(result["rendered_pages"]), 2)
            self.assertFalse(result["signing_sent"])
            self.assertTrue(result["visual_review_required"])
            self.assertTrue((root / "rendered" / "render-manifest.json").is_file())

    def test_invalid_dpi_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "preview.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            with pdf.open("wb") as stream:
                writer.write(stream)
            with self.assertRaisesRegex(ValueError, "dpi"):
                render(pdf, root / "rendered", dpi=20)


if __name__ == "__main__":
    unittest.main()
