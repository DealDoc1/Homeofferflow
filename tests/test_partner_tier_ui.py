import re
import unittest
from pathlib import Path


INDEX_PATH = Path(__file__).resolve().parents[1] / "index.html"


class PartnerTierUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX_PATH.read_text(encoding="utf-8")

    def test_three_public_tiers_and_rates_are_present(self):
        expected = (
            ("Market Listing", "$149"),
            ("Featured Partner", "$399"),
            ("Premier Market Sponsor", "$799"),
        )
        for label, rate in expected:
            with self.subTest(label=label):
                self.assertIn(label, self.html)
                self.assertIn(rate, self.html)

    def test_public_tiers_keep_existing_server_safe_model_values(self):
        for value in ("founding_pilot", "monthly_placement", "market_exclusive"):
            with self.subTest(value=value):
                self.assertRegex(
                    self.html,
                    rf'data-partner-tier="{re.escape(value)}"',
                )

    def test_consumer_choice_and_neutral_selection_are_explicit(self):
        required_copy = (
            "never preselects a paid provider",
            "users may choose any provider or none",
            "neutral provider selector",
            "Sponsored",
        )
        for copy in required_copy:
            with self.subTest(copy=copy):
                self.assertIn(copy, self.html)

    def test_partner_form_still_posts_to_existing_function(self):
        self.assertIn("fetch('/api/fsbo-lead'", self.html)
        self.assertIn("request_type: 'founding_partner'", self.html)


if __name__ == "__main__":
    unittest.main()
