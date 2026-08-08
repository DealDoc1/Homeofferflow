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
        self.assertIn("/api/fsbo-lead?partner_directory=1", self.html)
        self.assertIn("No active HomeOfferFlow provider profiles are available here yet.", self.html)
        self.assertIn("You are free to choose any provider or none.", self.html)

    def test_regulated_categories_are_neutral_and_not_sponsored(self):
        self.assertIn("NOW_WHAT_REGULATED_TYPES = new Set(['lender', 'title', 'inspection', 'surveyor'])", self.html)
        self.assertIn("HomeOfferFlow does not rank or preselect providers in these categories.", self.html)
        self.assertIn("regulated ? ''", self.html)

    def test_unregulated_partners_have_explicit_sponsored_label(self):
        self.assertIn("Premier Partner", self.html)
        self.assertIn("Featured Partner", self.html)
        self.assertIn("Sponsored · Core Partner", self.html)

    def test_directory_supports_local_search_category_filter_and_click_attribution(self):
        self.assertIn('id="nowWhatPartnerSearch"', self.html)
        self.assertIn('id="nowWhatPartnerCategory"', self.html)
        self.assertIn("window.__hofPartnerDirectoryRows", self.html)
        self.assertIn("partnerId:", self.html)


if __name__ == "__main__":
    unittest.main()
