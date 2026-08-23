import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class HomepageAudienceEntryTests(unittest.TestCase):
    def test_campaign_audience_deep_link_selects_only_supported_paths(self):
        self.assertIn("new URLSearchParams(window.location.search)", INDEX)
        self.assertIn(
            "new Set(['homebuyer', 'agent', 'investor', 'fsbo'])",
            INDEX,
        )
        self.assertIn("root.setAudience(landingAudience)", INDEX)
        self.assertIn("const utmAudience = campaignParams.get('utm_content')", INDEX)
        self.assertIn("const audienceParameter = explicitAudience ? 'audience' : (utmAudience ? 'utm_content' : '')", INDEX)

    def test_campaign_audience_is_measured_without_opening_a_wizard(self):
        self.assertIn("surface: 'campaign_deep_link'", INDEX)
        self.assertIn("root.trackEvent?.('Landing Audience Selected'", INDEX)
        self.assertIn("parameter: audienceParameter", INDEX)
        self.assertNotIn("beginOfferFrom('campaign_deep_link')", INDEX)


if __name__ == "__main__":
    unittest.main()
