from pathlib import Path
import importlib.util
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "api" / "fsbo-lead.py").read_text(encoding="utf-8")
API_PATH = ROOT / "api" / "fsbo-lead.py"
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
AGENTS = (ROOT / "agents.html").read_text(encoding="utf-8")
VERCEL = (ROOT / "vercel.json").read_text(encoding="utf-8")


class AgentLandingFunnelTests(unittest.TestCase):

    def test_passwordless_workspace_login_validates_and_focuses_email_before_requesting_auth(self):
        self.assertIn('id="authEmail" type="email" inputmode="email" autocomplete="email"', INDEX)
        start = INDEX.index("async function sendMagicLink()")
        end = INDEX.index("try {", start)
        entry = INDEX[start:end]
        self.assertIn("emailInput?.checkValidity()", entry)
        self.assertIn("emailInput?.focus();", entry)

    def test_searchable_agent_route_and_passwordless_entry_reuse_existing_workspace(self):
        self.assertIn('"source": "/agents"', VERCEL)
        self.assertIn('"destination": "/agents.html"', VERCEL)
        self.assertIn('href="/?agent=1"', AGENTS)
        self.assertIn('href="/agents"', INDEX)
        self.assertIn("if (params().get('agent') === '1')", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('agent')", INDEX)
        self.assertIn("window.openAuthModal?.('agent')", INDEX)

    def test_agent_landing_can_hand_off_directly_to_private_listing_tools(self):
        self.assertIn('href="/?agent=1&amp;workspace=seller"', AGENTS)
        self.assertIn("['seller', 'relationship'].includes(params().get('workspace'))", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_open_seller_workspace', '1')", INDEX)
        self.assertIn("tab: openSellerLandingWorkspace ? 'seller' : (openRelationshipLandingWorkspace ? 'relationships' : 'dashboard')", INDEX)
        self.assertIn("agent_landing_seller_workspace_handoff", INDEX)

    def test_agent_landing_can_hand_off_to_private_relationship_drafts(self):
        self.assertIn('href="/?agent=1&amp;workspace=relationship"', AGENTS)
        self.assertIn("hof_agent_landing_open_relationship_workspace", INDEX)
        self.assertIn("agent_landing_relationship_workspace_handoff", INDEX)
        self.assertIn("tab: 'relationships'", INDEX)
        self.assertIn('id="accountPanelRelationships"', INDEX)
        self.assertIn("preview-only until separate signing QA is complete", AGENTS)

    def test_relationship_drafts_are_a_persistent_agent_account_workspace(self):
        self.assertIn('id="relationshipsAccountTab"', INDEX)
        self.assertIn('data-account-tab="relationships"', INDEX)
        self.assertIn("onclick=\"showAccountTab('relationships')\"", INDEX)
        self.assertIn("normalized !== 'investor'", INDEX)
        self.assertIn("document.getElementById('accountPanelRelationships')", INDEX)
        self.assertIn("Prepare private, brokerage-approved relationship and consumer-notice drafts.", INDEX)

    def test_public_agent_copy_matches_the_draft_first_activation_path(self):
        self.assertIn('Start a client draft — no payment', AGENTS)
        self.assertIn('No password and no charge to start a private draft.', AGENTS)
        self.assertIn('save your agent defaults afterward for faster repeat offers', AGENTS)

    def test_agent_landing_preserves_the_safe_draft_request_through_sign_in(self):
        self.assertIn("hof_agent_landing_start_draft", INDEX)
        self.assertIn("const startAgentLandingDraft = localStorage.getItem('hof_agent_landing_start_draft') === '1';", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_start_draft', '1')", INDEX)
        self.assertIn("window.startAccountOffer?.();", INDEX)
        self.assertIn("agent_landing_draft_handoff", INDEX)

    def test_public_endpoint_and_page_record_only_allowlisted_aggregate_agent_landing_events(self):
        self.assertIn("AGENT_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_agent_landing_event(data):", API)
        self.assertIn('"agent_landing_viewed": "viewed"', API)
        self.assertIn('"agent_landing_cta_selected": "selected"', API)
        self.assertIn('"agent_workflow_guide_viewed": "viewed"', API)
        self.assertIn('"agent_workflow_guide_cta_selected": "selected"', API)
        self.assertIn("AGENT_LANDING_CHANNELS", API)
        self.assertIn("Unsupported agent landing channel.", API)
        self.assertIn('"channel": channel', API)
        self.assertIn("Unsupported agent landing event.", API)
        self.assertIn("'agent_landing_event'", API)
        self.assertIn('"surface": "agent_landing"', API)
        self.assertIn("sessionStorage.getItem(k)", AGENTS)
        self.assertIn("request_type:'agent_landing_event'", AGENTS)
        self.assertIn("agent_landing_viewed", AGENTS)
        self.assertIn("agent_landing_cta_selected", AGENTS)
        self.assertIn("new URLSearchParams(window.location.search).get('utm_source')", AGENTS)
        self.assertIn("'direct_outreach','email','social','referral','local_event','print'", AGENTS)
        self.assertIn("channel})", AGENTS)

    def test_agent_landing_channel_is_allowlisted_without_visitor_identity(self):
        spec = importlib.util.spec_from_file_location("agent_landing_channel", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = []
        with patch.object(api, "_record_partner_checkout_event", side_effect=lambda *args: captured.append(args)):
            api._record_agent_landing_event({"event_type": "agent_landing_cta_selected", "channel": "referral"})
            with self.assertRaisesRegex(ValueError, "Unsupported agent landing channel"):
                api._record_agent_landing_event({"event_type": "agent_landing_viewed", "channel": "untrusted"})
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][0], "agent_landing_cta_selected")
        self.assertEqual(captured[0][3], {"surface": "agent_landing", "role": "agent", "channel": "referral"})

    def test_admin_reports_agent_workspace_landing_conversion(self):
        for expected in (
            '"agentLandingViewCount"', '"agentLandingCtaCount"', '"agentLandingCtaRate"',
            '"agentLandingViewCountsByChannel"', '"agentLandingCtaCountsByChannel"',
            '"agentLandingDraftHandoffUserCount"', '"agentLandingDraftHandoffRate"',
            '"agentLandingSellerWorkspaceHandoffUserCount"',
            '"agentLandingRelationshipWorkspaceHandoffUserCount"',
            'agent_landing_draft_handoff',
            'agent_landing_seller_workspace_handoff',
            'agent_landing_relationship_workspace_handoff',
            'agentWorkflowGuideViewCount', 'agentWorkflowGuideCtaCount', 'agentWorkflowGuideCtaRate',
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("Agent Workspace Funnel", INDEX)
        self.assertIn("agentLandingCtaRate", INDEX)
        self.assertIn("Channel views / sign-ins", INDEX)
        self.assertIn("agentLandingViewCountsByChannel?.referral", INDEX)
        self.assertIn("agentLandingDraftHandoffUserCount", INDEX)
        self.assertIn("agentLandingDraftHandoffRate", INDEX)
        self.assertIn("agentLandingSellerWorkspaceHandoffUserCount", INDEX)
        self.assertIn("agentLandingRelationshipWorkspaceHandoffUserCount", INDEX)
        self.assertIn("Workspace paths after sign-in", INDEX)
        self.assertIn("agentWorkflowGuideCtaRate", INDEX)


if __name__ == "__main__":
    unittest.main()
