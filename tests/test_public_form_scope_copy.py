from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class PublicFormScopeCopyTests(unittest.TestCase):
    def test_public_footer_describes_supported_texas_workflows_without_erasing_txr_library(self):
        self.assertIn(
            "This tool supports the Texas real estate form workflows made available in HomeOfferFlow.",
            INDEX,
        )
        self.assertNotIn("This tool assists with completing official TREC forms only.", INDEX)


if __name__ == "__main__":
    unittest.main()
