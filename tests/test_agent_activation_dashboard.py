from pathlib import Path
import re
import unittest


INDEX_PATH = Path(__file__).resolve().parents[1] / "index.html"
HTML = INDEX_PATH.read_text(encoding="utf-8")


class AgentActivationDashboardTests(unittest.TestCase):
    def test_activation_card_is_present_in_dashboard(self):
        dashboard_start = HTML.index('id="accountPanelDashboard"')
        dashboard_end = HTML.index('id="accountPanelProfile"')
        dashboard = HTML[dashboard_start:dashboard_end]

        self.assertIn('id="agentActivationCard"', dashboard)
        self.assertLess(
            dashboard.index('id="agentActivationCard"'),
            dashboard.index('id="betaOnboardingChecklist"'),
        )

    def test_dashboard_waits_for_offers_before_rendering_activation_state(self):
        function_match = re.search(
            r"async function openAccountDashboard\(opts = \{\}\) \{(?P<body>.*?)\n  \}",
            HTML,
            re.DOTALL,
        )
        self.assertIsNotNone(function_match)
        body = function_match.group("body")

        self.assertIn("await loadMyOffers();", body)
        self.assertLess(body.index("await loadMyOffers();"), body.index("renderAccountDashboard();"))

    def test_offer_loader_persists_offer_state_for_activation_card(self):
        self.assertIn("hofAuth.myOffers = data || [];", HTML)
        self.assertIn("renderAgentActivationCard();", HTML)

    def test_offer_detail_queries_are_explicitly_scoped_to_the_signed_in_owner(self):
        self.assertGreaterEqual(
            HTML.count(".from('hof_offers').select('*').eq('user_id', user.id).eq('id', offerId).maybeSingle()"),
            2,
        )

    def test_activation_funnel_has_profile_offer_and_subscription_steps(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        for expected in (
            "Profile and defaults",
            "First saved offer",
            "Active subscription",
            "Agent Activation Dashboard Viewed",
            "Agent Activation Action",
        ):
            self.assertIn(expected, script)

    def test_profile_activation_requires_agent_contact_and_license_fields(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        for field in (
            "profile.agent_name",
            "profile.license_number",
            "profile.agent_email",
            "profile.agent_phone",
            "profile.brokerage_name",
        ):
            self.assertIn(field, script)

    def test_activation_actions_cover_primary_account_paths(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        for action in ("profile", "new_offer", "offers", "resume", "subscribe"):
            self.assertRegex(script, rf"action === ['\"]{action}['\"]")

    def test_legacy_demo_card_is_removed_by_final_dashboard_renderer(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("release15DashboardCard", script)
        self.assertIn("?.remove()", script)


if __name__ == "__main__":
    unittest.main()
