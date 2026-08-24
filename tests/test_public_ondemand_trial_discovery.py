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

        self.assertIn('href="/ondemand?utm_source=agent_workspace', agent_copy)
        self.assertIn('utm_source=agent_workspace&amp;utm_medium=workspace&amp;utm_campaign=agent_acquisition', agent_copy)
        self.assertIn("OnDemand Realty agent? Start your 60-day free trial", agent_copy)
        self.assertIn("card required", agent_copy)
        self.assertIn("recordOnDemandTrialEntry", agent_copy)

    def test_agent_path_surfaces_a_dedicated_trial_cta_without_showing_it_to_other_audiences(self):
        self.assertIn("function syncOnDemandHeroTrialCta(type)", INDEX)
        self.assertIn("if (type !== 'agent')", INDEX)
        self.assertIn("onDemandHeroTrialCta", INDEX)
        self.assertIn("OnDemand agent? Start 60 days free", INDEX)
        self.assertIn("agent_hero_secondary_cta", INDEX)
        self.assertIn("agent_hero_inline", INDEX)
        self.assertIn("function recordOnDemandTrialEntry", INDEX)
        self.assertIn("ondemand_trial_entry_selected", INDEX)
        self.assertIn("request_type: 'ondemand_landing_event'", INDEX)
        self.assertIn("hof_ondemand_trial_entry_selected", INDEX)

    def test_beta_subscription_card_surfaces_trial_only_for_agent_role(self):
        start = INDEX.index("} else {\n      actionHtml =", INDEX.index("function renderSubscriptionCard"))
        end = INDEX.index("    card.innerHTML = `", start)
        beta_branch = INDEX[start:end]
        self.assertIn("role === 'agent'", beta_branch)
        self.assertIn("agent_subscription_card", beta_branch)
        self.assertIn("OnDemand: 60 days free", beta_branch)
        self.assertIn("card required, then $29/month unless canceled", beta_branch)


if __name__ == "__main__":
    unittest.main()
