from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class PartnerDirectoryImpressionTests(unittest.TestCase):
    def test_partner_directory_tracks_privacy_safe_deduplicated_impressions(self):
        self.assertIn("trackPartnerDirectoryImpressions", HTML)
        self.assertIn("Partner Directory Impression", HTML)
        self.assertIn("hof_partner_impression_", HTML)
        self.assertIn("Partner Directory Outbound Click", HTML)
        self.assertIn("sessionStorage", HTML)


if __name__ == "__main__":
    unittest.main()
