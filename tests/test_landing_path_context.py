import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class LandingPathContextTests(unittest.TestCase):
    def test_shared_landing_sections_are_updated_for_each_customer_path(self):
        self.assertIn("function syncLandingPathContext(type)", HTML)
        self.assertIn("syncLandingPathContext(type);", HTML)
        self.assertIn("From transaction type to one organized package.", HTML)
        self.assertIn("From two details to a clear seller plan.", HTML)
        self.assertIn("From repeat deal details to a clean offer packet.", HTML)

    def test_agent_path_does_not_present_buyer_payment_or_brokerage_seat_as_required(self):
        self.assertIn("Do I need a brokerage seat to use this?", HTML)
        self.assertIn("Available to every signed-in agent.", HTML)
        self.assertIn("A personal workspace does not require a brokerage seat", HTML)
        self.assertIn("They remain private drafts for your review.", HTML)
        self.assertIn("Ready to start a transaction?", HTML)

    def test_seller_path_keeps_the_first_step_short_and_commitment_free(self):
        self.assertIn("From two details to a clear seller plan.", HTML)
        self.assertIn("There is no checkout or commitment to choose a service.", HTML)
        self.assertIn("Ready to start your free seller plan?", HTML)
        self.assertIn("Start with your address and email. It takes under a minute", HTML)


if __name__ == "__main__":
    unittest.main()
