import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class SeoHeroUpdateTests(unittest.TestCase):
    def test_homebuyer_hero_uses_the_approved_plain_english_positioning(self):
        self.assertIn(
            "Write a Real Estate Offer<br/><em>Without the Confusion.</em>", INDEX
        )
        self.assertIn("Write a Real Estate Offer Without the Confusion | HomeOfferFlow", INDEX)
        self.assertIn('name="description"', INDEX)
        self.assertIn(
            "supported Texas buyer-offer packet in plain English", INDEX
        )
        self.assertIn("Texas real estate offer builder", INDEX)

    def test_agent_copy_does_not_overstate_current_form_coverage(self):
        self.assertIn("Texas real estate documents, <em>made simpler.</em>", INDEX)
        self.assertIn(
            "Start with the transaction in front of you. Answer a few clear questions, then review one organized document package.",
            INDEX,
        )
        self.assertIn(
            "Choose the transaction in front of you, answer clear questions, and review one organized document package.",
            INDEX,
        )
        self.assertIn("Available to every signed-in agent.", INDEX)
        self.assertNotIn("listing agreements remain outside the stated live scope", INDEX)

    def test_supported_trec_offer_scope_is_described_on_the_landing_page(self):
        self.assertIn("We prepare the supported forms", INDEX)
        self.assertIn("purchase addenda currently supported by HomeOfferFlow", INDEX)


if __name__ == "__main__":
    unittest.main()
