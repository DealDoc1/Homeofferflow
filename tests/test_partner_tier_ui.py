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
            ("Core Partner", "$149"),
            ("Featured Partner", "$399"),
            ("Premier Partner", "$799"),
        )
        for label, rate in expected:
            with self.subTest(label=label):
                self.assertIn(label, self.html)
                self.assertIn(rate, self.html)

    def test_founder_offer_is_a_clear_nonrenewing_90_day_pilot(self):
        required_copy = (
            "first 90 days for the price of one standard month",
            "first 10 approved partners",
            "no setup fee",
            "then renews monthly at the standard rate after 90 days unless cancelled",
            "Then $149/month after 90 days, unless cancelled",
            "Then $399/month after 90 days, unless cancelled",
            "Then $799/month after 90 days, unless cancelled",
        )
        for copy in required_copy:
            with self.subTest(copy=copy):
                self.assertIn(copy, self.html)

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

    def test_homepage_audience_grid_links_to_partner_offer(self):
        self.assertIn("<h3>Service Partners</h3>", self.html)
        self.assertIn("Founding partner placements from $149", self.html)
        self.assertRegex(
            self.html,
            r'class="audience-card audience-card-link"[^>]+href="\?partner=1"',
        )
        self.assertIn("openFoundingPartnerModal();", self.html)

    def test_partner_category_list_includes_roofing_and_home_services(self):
        expected_categories = (
            ('roofing', 'Roofing contractor'),
            ('hvac', 'HVAC / heating and air'),
            ('plumbing', 'Plumbing'),
            ('electrical', 'Electrical'),
            ('foundation_structural', 'Foundation / structural repair'),
            ('general_contractor', 'General contractor / remodeling'),
            ('pest_termite', 'Pest control / termite'),
            ('septic_well', 'Septic / well service'),
            ('restoration', 'Water / fire restoration'),
            ('surveyor', 'Property surveyor'),
            ('security_smart_home', 'Security / smart home'),
        )
        for value, label in expected_categories:
            with self.subTest(value=value):
                self.assertIn(
                    f'<option value="{value}">{label}</option>',
                    self.html,
                )


if __name__ == "__main__":
    unittest.main()
