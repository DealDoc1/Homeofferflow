"""Public investor messaging must reflect the workflow that is actually available."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class InvestorWorkspaceCopyTests(unittest.TestCase):
    def test_investor_copy_describes_live_saved_defaults_and_repeat_offer_tools(self):
        self.assertIn("Save investor defaults and duplicate prior offers", HTML)
        self.assertIn("Save deal defaults, duplicate prior offers", HTML)

    def test_investor_copy_does_not_describe_live_features_as_coming_soon(self):
        self.assertNotIn("Saved investor profiles and repeat-offer tools are coming soon", HTML)
        self.assertNotIn("Investor saved profiles and repeat-offer tools are coming soon", HTML)


if __name__ == "__main__":
    unittest.main()
