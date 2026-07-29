from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LandingMarketingCopyTests(unittest.TestCase):
    def test_homebuyer_hero_states_the_current_texas_offer_value(self):
        self.assertIn("Write a Real Estate <em>Offer</em><br/>Without the Confusion.", HTML)
        self.assertIn("No agent? No problem.", HTML)
        self.assertIn("mobile-friendly way to prepare a Texas offer packet", HTML)

    def test_agent_copy_discloses_live_plan_and_ondemand_trial(self):
        self.assertIn("Agent plans are $29/month", HTML)
        self.assertIn("OnDemand Realty agents receive 60 days free", HTML)

    def test_supported_form_scope_is_not_overstated(self):
        self.assertIn("the addenda HomeOfferFlow supports for your selected terms", HTML)


if __name__ == "__main__":
    unittest.main()
