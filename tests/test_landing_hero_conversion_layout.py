from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LandingHeroConversionLayoutTests(unittest.TestCase):
    def test_primary_cta_is_protected_from_an_oversized_desktop_hero(self):
        self.assertIn("min-height: min(100vh, 760px)", HTML)
        self.assertIn("font-size: clamp(2.55rem, 6.2vw, 4.6rem)", HTML)
        self.assertIn(".hero-actions { display: flex; gap: 1rem; margin-top: 1.5rem", HTML)
        self.assertIn('id="heroCta"', HTML)
        self.assertIn("Start Your Offer — $99", HTML)

    def test_public_offer_ctas_record_a_non_sensitive_conversion_surface(self):
        for surface in (
            "landing_nav_cta",
            "landing_hero_cta",
            "landing_bottom_cta",
            "landing_audience_card_homebuyer",
            "landing_audience_card_agent",
            "landing_audience_card_investor",
        ):
            self.assertIn(f"beginOfferFrom('{surface}')", HTML)
        self.assertIn("function beginOfferFrom(surface)", HTML)
        self.assertIn("Offer Entry CTA Selected", HTML)
        self.assertIn("window.__hofOfferEntrySurface", HTML)
        self.assertIn("entrySurface: window.__hofOfferEntrySurface || 'direct'", HTML)


if __name__ == "__main__":
    unittest.main()
