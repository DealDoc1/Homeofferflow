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

    def test_agent_copy_does_not_overstate_current_form_coverage(self):
        self.assertIn("Write supported Texas <em>offers faster</em>.", INDEX)
        self.assertIn(
            "Representation and notice forms are in private preview foundations; listing and seller-form signing workflows are not live yet.",
            INDEX,
        )

    def test_supported_trec_offer_scope_is_described_on_the_landing_page(self):
        self.assertIn("We prepare the supported forms", INDEX)
        self.assertIn("purchase addenda currently supported by HomeOfferFlow", INDEX)


if __name__ == "__main__":
    unittest.main()
