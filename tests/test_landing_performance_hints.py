from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class LandingPerformanceHintTests(unittest.TestCase):
    def test_primary_landing_preconnects_the_font_origins_it_uses(self):
        self.assertIn('<link rel="preconnect" href="https://fonts.googleapis.com" />', INDEX)
        self.assertIn('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />', INDEX)
        self.assertLess(
            INDEX.index('rel="preconnect" href="https://fonts.googleapis.com"'),
            INDEX.index('href="https://fonts.googleapis.com/css2?family=Playfair+Display'),
        )

    def test_google_fonts_query_is_valid_html(self):
        start = INDEX.index('href="https://fonts.googleapis.com/css2?family=Playfair+Display')
        end = INDEX.index('"', start + len('href="'))
        font_href = INDEX[start:end]
        self.assertIn('&amp;family=DM+Sans', font_href)
        self.assertIn('&amp;display=swap', font_href)
        self.assertNotIn('&family=', font_href)


if __name__ == "__main__":
    unittest.main()
