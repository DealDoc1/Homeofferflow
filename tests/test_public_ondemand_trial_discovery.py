import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class PublicOnDemandTrialDiscoveryTests(unittest.TestCase):
    def test_agent_landing_path_links_only_ondemand_agents_to_the_dedicated_trial(self):
        audience_copy_start = INDEX.index("const oldSetAudience = root.setAudience")
        agent_start = INDEX.index("agent: {", audience_copy_start)
        investor_start = INDEX.index("investor: {", agent_start)
        agent_copy = INDEX[agent_start:investor_start]

        self.assertIn('href="/ondemand"', agent_copy)
        self.assertIn("OnDemand Realty agent? Start your 60-day free trial", agent_copy)
        self.assertIn("card required", agent_copy)
        self.assertIn("OnDemand Trial Link Selected", agent_copy)

    def test_agent_path_surfaces_a_dedicated_trial_cta_without_showing_it_to_other_audiences(self):
        self.assertIn("function syncOnDemandHeroTrialCta(type)", INDEX)
        self.assertIn("if (type !== 'agent')", INDEX)
        self.assertIn("onDemandHeroTrialCta", INDEX)
        self.assertIn("OnDemand agent? Start 60 days free", INDEX)
        self.assertIn("surface: 'agent_hero_secondary_cta'", INDEX)


if __name__ == "__main__":
    unittest.main()
