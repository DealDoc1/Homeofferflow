from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LandingHeroConversionLayoutTests(unittest.TestCase):
    def test_primary_cta_is_protected_from_an_oversized_desktop_hero(self):
        self.assertIn("min-height: min(100vh, 760px)", HTML)
        self.assertIn("font-size: clamp(2.55rem, 6.2vw, 4.6rem)", HTML)
        self.assertIn(".hero-actions { display: flex; gap: 1rem; margin-top: 1.5rem", HTML)
        self.assertIn('id="heroCta"', HTML)
        self.assertIn("Build Your Offer — No Payment to Start", HTML)

    def test_homebuyer_cta_matches_the_no_payment_before_review_promise(self):
        self.assertIn(
            "Build Your Offer — No Payment to Start",
            HTML[HTML.index('<section class=\"hero\">'):HTML.index('</section>', HTML.index('<section class=\"hero\">'))],
        )
        self.assertIn(
            "cta: 'Build Your Offer — No Payment to Start'",
            HTML,
        )
        self.assertIn(
            'id="bottomCta" onclick="beginOfferFrom(\'landing_bottom_cta\')">Build Your Offer — No Payment to Start</button>',
            HTML,
        )
        self.assertIn("the homebuyer offer packet is $99 only when ready.", HTML)

    def test_public_offer_ctas_record_a_non_sensitive_conversion_surface(self):
        for surface in (
            "landing_nav_cta",
            "landing_hero_cta",
            "landing_bottom_cta",
            "landing_audience_card_homebuyer",
            "landing_audience_card_investor",
        ):
            self.assertIn(f"beginOfferFrom('{surface}')", HTML)
        self.assertIn("function beginOfferFrom(surface)", HTML)
        self.assertIn("Offer Entry CTA Selected", HTML)
        self.assertIn("window.__hofOfferEntrySurface", HTML)
        self.assertIn("entrySurface: window.__hofOfferEntrySurface || 'direct'", HTML)
        self.assertIn("const buyerEntrySurface = buyerRouteParams.get('utm_source') === 'texas_homebuyer_offer_guide'", HTML)
        self.assertIn("? 'texas_homebuyer_offer_guide'", HTML)
        self.assertIn("window.beginOfferFrom?.(buyerEntrySurface);", HTML)

    def test_agent_audience_card_routes_to_the_transaction_first_agent_page(self):
        self.assertIn("window.location.assign('/agents')", HTML)
        self.assertIn('Start with property listing, purchase, lease listing, or tenant representation', HTML)


if __name__ == "__main__":
    unittest.main()
