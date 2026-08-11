from pathlib import Path
import re
import unittest


INDEX_PATH = Path(__file__).resolve().parents[1] / "index.html"
HTML = INDEX_PATH.read_text(encoding="utf-8")


class AgentActivationDashboardTests(unittest.TestCase):
    def test_platform_admin_exposes_aggregate_agent_activation_metrics_only(self):
        api = (INDEX_PATH.parent / "api" / "admin-dashboard.py").read_text(encoding="utf-8")

        for expected in (
            "agentProfileCompleteCount",
            "agentFirstOfferCount",
            "agentRepeatOfferCount",
            "agentUpdatedDraftCount",
        ):
            self.assertIn(expected, api)

        self.assertIn(
            "hof_offers?role=eq.agent&deleted_at=is.null&select=user_id,status,signwell_status,created_at,updated_at",
            api,
        )
        self.assertNotIn("buyer_name", api[api.index("agent_lifecycle_offers"):api.index("events =")])

    def test_platform_admin_renders_agent_activation_funnel_metrics(self):
        for expected in (
            "Agent Profiles Ready",
            "Agents With a Saved Offer",
            "Repeat-Offer Agents",
            "Updated Agent Drafts",
        ):
            self.assertIn(expected, HTML)

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

    def test_first_offer_is_the_primary_value_step_before_profile_defaults(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        first_offer = script.index("if (!hasOffer) {")
        profile_after_offer = script.index("if (!hasProfile) {", first_offer + 1)
        self.assertLess(first_offer, profile_after_offer)
        self.assertIn("Start your first client offer", script)
        self.assertIn("Start First Offer", script)
        self.assertIn("Set Up My Defaults", script)

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

    def test_activation_actions_record_stage_and_primary_or_secondary_choice(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("activationKey", script)
        self.assertIn("control === 'primary' || control === 'secondary'", script)
        self.assertIn("'primary','${safe(state.key)}'", script)
        self.assertIn("'secondary','${safe(state.key)}'", script)

    def test_active_subscription_keeps_next_offer_action_visible(self):
        subscription_start = HTML.index("function renderSubscriptionCard()")
        subscription_end = HTML.index("async function openBillingPortal", subscription_start)
        subscription = HTML[subscription_start:subscription_end]

        self.assertIn("const remaining = Math.max(0, limit - used);", subscription)
        self.assertIn('Create Next Offer', subscription)
        self.assertIn("remaining + ' packet'", subscription)
        self.assertIn("startAccountOffer()", subscription)

    def test_legacy_demo_card_is_removed_by_final_dashboard_renderer(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("release15DashboardCard", script)
        self.assertIn("?.remove()", script)


if __name__ == "__main__":
    unittest.main()
