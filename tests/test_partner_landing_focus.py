import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PartnerLandingFocusTests(unittest.TestCase):
    def test_partner_guide_is_progressively_quieted_without_removing_it(self):
        page = (ROOT / 'partners.html').read_text(encoding='utf-8')
        script = (ROOT / 'assets/partner-landing-focus.js').read_text(encoding='utf-8')
        self.assertIn('/assets/partner-landing-focus.css', page)
        self.assertIn('/assets/partner-landing-focus.js', page)
        self.assertIn('texas-home-service-partner-guide', page)
        self.assertIn('Want the short version first?', script)
        self.assertIn('Read the short partner placement guide', script)
        self.assertIn('partner_guide_expanded', script)
        self.assertIn('pwa_shortcut', script)


if __name__ == '__main__':
    unittest.main()
