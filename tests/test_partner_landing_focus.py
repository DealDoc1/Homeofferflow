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
        self.assertIn("rawMedium === 'organic_content'", script)
        self.assertIn("'direct_outreach'", script)
        self.assertIn("'owned_directory'", script)

    def test_partner_landing_clearly_states_free_beta_application_path(self):
        page = (ROOT / 'partners.html').read_text(encoding='utf-8')
        self.assertIn('class="skip-link" href="#tiers"', page)
        self.assertIn('.skip-link:focus', page)
        self.assertIn('HomeOfferFlow connects Texas buyers, sellers, agents, and investors', page)
        self.assertIn('Start free application', page)
        self.assertIn('Every partner placement is complimentary during beta.', page)
        self.assertIn('No checkout, payment, or automatic paid conversion applies.', page)
        self.assertNotIn('secure checkout', page.lower())


if __name__ == '__main__':
    unittest.main()
