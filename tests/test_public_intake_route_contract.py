import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
PAGES = {
    "buyers": (ROOT / "buyers.html").read_text(encoding="utf-8"),
    "sellers": (ROOT / "sellers.html").read_text(encoding="utf-8"),
    "agents": (ROOT / "agents.html").read_text(encoding="utf-8"),
    "investors": (ROOT / "investors.html").read_text(encoding="utf-8"),
}


class PublicIntakeRouteContractTests(unittest.TestCase):
    def test_public_audiences_have_canonical_landing_pages(self):
        for route, page in PAGES.items():
            with self.subTest(route=route):
                self.assertIn(
                    f'<link rel="canonical" href="https://www.homeofferflow.com/{route}"',
                    page,
                )

    def test_each_public_landing_hands_off_to_its_own_workflow(self):
        self.assertIn('href="/?buyer=1"', PAGES["buyers"])
        self.assertIn('href="/?seller=1', PAGES["sellers"])
        self.assertIn('href="/?agent=1&amp;workflow=purchase', PAGES["agents"])
        self.assertIn('href="/?investor=1"', PAGES["investors"])

    def test_homepage_keeps_a_distinct_entry_for_each_customer_type(self):
        for audience in ("homebuyer", "agent", "investor", "fsbo"):
            self.assertIn(f'data-audience="{audience}"', INDEX)

        start = INDEX.index("function beginOfferFrom(surface)")
        end = INDEX.index("function startPrimaryOffer()", start)
        handoff = INDEX[start:end]
        self.assertIn("window.location.assign('/agents?", handoff)
        self.assertIn("window.location.assign('/?investor=1", handoff)
        self.assertIn("rememberHomebuyerCheckoutChannel()", handoff)

    def test_agent_transaction_question_preserves_all_four_supported_paths(self):
        for workflow, label in (
            ("sale_listing", "Property listing"),
            ("purchase", "Purchase"),
            ("lease_listing", "Lease listing"),
            ("lease_representation", "Tenant representation"),
        ):
            self.assertIn(f'data-agent-workflow-choice="{workflow}"', INDEX)
            self.assertIn(f"startAgentWorkflow('{workflow}')", INDEX)
            self.assertIn(label, PAGES["agents"])

    def test_buyer_entry_never_requires_agent_authentication(self):
        start = INDEX.index("function startHomebuyerOffer()")
        end = INDEX.index("function resumableLocalOfferDraft()", start)
        homebuyer_start = INDEX[start:end]
        self.assertIn("resetWizardForFreshOffer('homebuyer')", homebuyer_start)
        self.assertIn("openWizard(true)", homebuyer_start)
        self.assertNotIn("openAuthModal", homebuyer_start)


if __name__ == "__main__":
    unittest.main()
