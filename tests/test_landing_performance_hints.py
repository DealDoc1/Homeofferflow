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


if __name__ == "__main__":
    unittest.main()
