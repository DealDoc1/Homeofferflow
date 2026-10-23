import unittest
from pathlib import Path


HTML_PATH = Path(__file__).resolve().parents[1] / "index.html"


class NowWhatPartnerJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")

    def test_success_screen_contains_platform_wide_now_what_journey(self):
        self.assertIn('id="nowWhatPartnerJourney"', self.html)
        self.assertIn('Now what?', self.html)
        self.assertIn('Your transaction, your choices', self.html)
        self.assertIn('renderNowWhatPartnerJourney();', self.html)

    def test_directory_uses_public_platform_endpoint(self):
        self.assertIn("renderNowWhatDirectory(await window.hofPartnerProfile.load('workflow'));", self.html)
        self.assertIn("surface === 'workflow' ? 'workflow' : 'directory'", (HTML_PATH.parent/'assets/partner-profile.js').read_text())
        self.assertIn("No active HomeOfferFlow provider profiles are available here yet.", self.html)
        self.assertIn("You are free to choose any provider or none.", self.html)

    def test_completion_directory_only_mentions_the_single_platform_top_premier(self):
        self.assertIn("window.hofPartnerProfile.load('workflow')", self.html)
        self.assertIn('window.hofPartnerProfile.placementLabel(partner)', self.html)
        api = (HTML_PATH.parent/'api/fsbo-lead.py').read_text(encoding='utf-8')
        self.assertIn('return premier[:1]', api)
        self.assertIn('partners = partners[:3]', api)
        self.assertIn('single top active Premier across HomeOfferFlow', (HTML_PATH.parent/'partners.html').read_text(encoding='utf-8'))

    def test_premier_partners_have_explicit_tier_label(self):
        self.assertIn("Premier Partner", self.html)
        self.assertIn("Featured Partner", self.html)
        self.assertIn("placementLabel(partner)", self.html)

    def test_directory_supports_local_search_category_filter_and_click_attribution(self):
        self.assertIn('id="nowWhatPartnerSearch"', self.html)
        self.assertIn('id="nowWhatPartnerCategory"', self.html)
        self.assertIn("window.__hofPartnerDirectoryRows", self.html)
        self.assertIn("partnerId:", self.html)
        self.assertIn("recordOfferCompletionPartnerDirectoryEvent", self.html)
        self.assertIn("directory_surface: 'offer_completion'", self.html)


if __name__ == "__main__":
    unittest.main()
