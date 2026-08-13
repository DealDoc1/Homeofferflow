from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
PUBLIC_DIRECTORY = (ROOT / "directory.html").read_text(encoding="utf-8")


class PartnerDirectoryImpressionTests(unittest.TestCase):
    def test_partner_directory_tracks_privacy_safe_deduplicated_impressions(self):
        self.assertIn("trackPartnerDirectoryImpressions", HTML)
        self.assertIn("Partner Directory Impression", HTML)
        self.assertIn("hof_partner_impression_", HTML)
        self.assertIn("Partner Directory Outbound Click", HTML)
        self.assertIn("sessionStorage", HTML)

    def test_public_directory_uses_the_same_privacy_safe_partner_events(self):
        self.assertIn("Partner Directory Impression", PUBLIC_DIRECTORY)
        self.assertIn("Partner Directory Outbound Click", PUBLIC_DIRECTORY)
        self.assertIn("hof_public_partner_impression_", PUBLIC_DIRECTORY)
        self.assertIn("data-partner-link", PUBLIC_DIRECTORY)
        self.assertIn('/_vercel/insights/script.js', PUBLIC_DIRECTORY)

    def test_public_directory_records_category_demand_without_market_text(self):
        self.assertIn('trackSearchDemand', PUBLIC_DIRECTORY)
        self.assertIn('Provider Directory Search', PUBLIC_DIRECTORY)
        self.assertIn("category:safeCategory, hasMarket", PUBLIC_DIRECTORY)
        self.assertIn("hof_public_directory_search_${safeCategory}_${hasMarket ? 'market' : 'all'}", PUBLIC_DIRECTORY)
        self.assertNotIn("market:market", PUBLIC_DIRECTORY)


if __name__ == "__main__":
    unittest.main()
