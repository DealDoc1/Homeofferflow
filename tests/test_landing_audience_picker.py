from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LandingAudiencePickerTests(unittest.TestCase):
    def test_hero_paths_are_keyboard_accessible_buttons_with_selection_state(self):
        hero = HTML[HTML.index('<section class="hero">'):HTML.index('</section>', HTML.index('<section class="hero">'))]
        self.assertIn('role="group" aria-label="Choose your HomeOfferFlow path"', hero)
        for audience in ("homebuyer", "agent", "investor", "fsbo"):
            with self.subTest(audience=audience):
                self.assertIn(f'<button type="button" class="pill', hero)
                self.assertIn(f'data-audience="{audience}"', hero)
                self.assertIn(f"audience: '{audience}'", hero)
        self.assertIn("p.setAttribute('aria-pressed', selected ? 'true' : 'false');", HTML)
        self.assertIn('.pill:focus-visible', HTML)

    def test_path_selection_telemetry_stays_aggregate_only(self):
        hero = HTML[HTML.index('<section class="hero">'):HTML.index('</section>', HTML.index('<section class="hero">'))]
        self.assertEqual(hero.count("Landing Audience Selected"), 4)
        self.assertIn("surface: 'hero_path_picker'", hero)
        self.assertNotIn("email", hero.lower())
        self.assertNotIn("address", hero.lower())

    def test_platform_admin_receives_only_fixed_audience_selection_aggregates(self):
        backend = (Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"landingAudienceSelectionCount"', backend)
        self.assertIn('"landingAudienceSelectionCounts"', backend)
        self.assertIn('landing_audience_selection_counts', backend)
        self.assertIn('if audience in landing_audience_selection_counts:', backend)
        self.assertIn("Landing Path Selections", HTML)
        self.assertIn("Aggregate routing interest only", HTML)


if __name__ == "__main__":
    unittest.main()
