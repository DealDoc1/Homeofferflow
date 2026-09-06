from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class NeutralTitleSelectionTests(unittest.TestCase):
    def test_homebuyer_interview_does_not_preselect_a_specific_title_or_escrow_provider(self):
        for provider_name in (
            "Forgey Law Group - Chicago Title Frisco",
            "Kate Lewis Tucker - Chicago Title DFW",
            "Chicago Title DFW - Forgey Law Group PLLC",
        ):
            self.assertNotIn(provider_name, HTML)

        self.assertIn('id="titleCompany" placeholder="e.g. Alamo Title Company"', HTML)
        self.assertIn('id="escrowAgent" placeholder="e.g. Alamo Title Company"', HTML)
        self.assertIn('id="escrowAddress" placeholder="Street address of title company"', HTML)
        self.assertNotIn("HOF_HOMEBUYER_DEFAULTS", HTML)
        self.assertNotIn("applyHomebuyerTitleDefaults", HTML)

    def test_signed_in_agents_and_investors_can_still_use_their_own_saved_defaults(self):
        self.assertIn("p.preferred_title_company", HTML)
        self.assertIn("p.preferred_escrow_agent || p.preferred_title_company", HTML)
        self.assertIn("p.preferred_escrow_address", HTML)


if __name__ == "__main__":
    unittest.main()
