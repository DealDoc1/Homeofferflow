from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BrokerageBrandPreviewTests(unittest.TestCase):
    def test_branding_controls_include_live_preview(self):
        self.assertIn("renderBrokerageBrandPreview", HTML)
        self.assertIn("brokerageBrandPreview", HTML)
        self.assertIn("Prepared through HomeOfferFlow", HTML)
        self.assertIn("Offer packet + email touchpoint", HTML)
        self.assertIn("oninput=\"renderBrokerageBrandPreview()\"", HTML)
        self.assertIn("onchange=\"renderBrokerageBrandPreview()\"", HTML)


if __name__ == "__main__":
    unittest.main()
