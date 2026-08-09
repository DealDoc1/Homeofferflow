import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrokerageBrandingMetricTests(unittest.TestCase):
    def test_branding_funnel_events_are_privacy_safe(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("brokerage_branding_preview_viewed", source)
        self.assertIn("brokerage_branding_save_started", source)
        self.assertIn("brokerage_branding_saved", source)
        self.assertIn("brokerage_branding_save_failed", source)
        self.assertIn("hasLogo", source)
        self.assertNotIn("logoFileName", source)


if __name__ == "__main__":
    unittest.main()
