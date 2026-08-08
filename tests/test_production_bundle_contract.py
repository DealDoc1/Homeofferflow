import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ProductionBundleContractTests(unittest.TestCase):
    def test_legacy_20_18_source_is_not_bundled(self):
        ignore = (ROOT / ".vercelignore").read_text(encoding="utf-8")
        self.assertIn("20-18_0.pdf", ignore)

    def test_production_route_points_to_20_19(self):
        source = (ROOT / "api" / "fill-pdf.py").read_text(encoding="utf-8")
        self.assertIn('MAIN_PDF      = os.path.join(BASE_DIR, "20-19_0.pdf")', source)
        self.assertIn('"trec_main_form": "20-19 production"', source)
        self.assertNotIn('MAIN_PDF      = os.path.join(BASE_DIR, "20-18_0.pdf")', source)


if __name__ == "__main__":
    unittest.main()
