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
    def test_each_public_transaction_choice_is_a_full_card_tap_target(self):
        self.assertEqual(AGENTS.count('class="card transaction-card" data-agent-cta-path='), 4)
        self.assertIn('.transaction-card{display:block;', AGENTS)
        self.assertIn('.transaction-card:focus-visible', AGENTS)
        self.assertNotIn('<article class="card"><h3>Buying</h3>', AGENTS)


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
        self.assertIn('href="/?agent=1&amp;workflow=purchase"', AGENTS)
        self.assertIn('href="/agents"', INDEX)
        self.assertIn("if (params().get('agent') === '1')", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('agent')", INDEX)
        self.assertIn("window.openAuthModal?.('agent')", INDEX)

    def test_agent_landing_uses_transaction_choices_for_listing_handoffs(self):
        self.assertIn('href="/?agent=1&amp;workflow=sale_listing"', AGENTS)
        self.assertIn('href="/?agent=1&amp;workflow=lease_listing"', AGENTS)
        self.assertIn("window.hofAgentWorkflowContext = agentLandingWorkflow", INDEX)
        self.assertIn("agent_landing_seller_workspace_handoff", INDEX)

    def test_agent_landing_can_start_each_transaction_in_its_relevant_workspace(self):
        for workflow, cta_path in (
            ("purchase", "client_draft"),
            ("sale_listing", "seller_listing"),
            ("lease_listing", "lease_listing"),
            ("lease_representation", "lease_representation"),
        ):
            self.assertIn(f'workflow={workflow}', AGENTS)
            self.assertIn(f'data-agent-cta-path="{cta_path}"', AGENTS)
        self.assertIn("const agentLandingWorkflow = ['purchase', 'sale_listing', 'lease_listing', 'lease_representation']", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_workflow', agentLandingWorkflow)", INDEX)
        self.assertIn("window.hofAgentWorkflowContext = agentLandingWorkflow", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('workflow')", INDEX)

    def test_agent_landing_uses_lease_representation_for_relationship_draft_handoffs(self):
        self.assertIn('href="/?agent=1&amp;workflow=lease_representation"', AGENTS)
        self.assertIn("hof_agent_landing_open_relationship_workspace", INDEX)
        self.assertIn("agent_landing_relationship_workspace_handoff", INDEX)
        self.assertIn("tab: 'relationships'", INDEX)
        self.assertIn('id="accountPanelRelationships"', INDEX)
        self.assertIn("private TXR-1501, TXR-1506, TXR-1507, TXR-1508, TXR-1905, TXR-1914, TXR-1917, and TXR-1919 review-draft creation for every signed-in agent", AGENTS)

    def test_relationship_drafts_are_a_persistent_agent_account_workspace(self):
        self.assertIn('id="relationshipsAccountTab"', INDEX)
        self.assertIn('data-account-tab="relationships"', INDEX)
        self.assertIn("onclick=\"showAccountTab('relationships')\"", INDEX)
        self.assertIn("normalized !== 'investor'", INDEX)
        self.assertIn("document.getElementById('accountPanelRelationships')", INDEX)
        self.assertIn("Prepare private, brokerage-approved relationship and consumer-notice drafts.", INDEX)

    def test_relationship_workspace_explains_each_private_draft_without_selecting_a_form(self):
        self.assertIn('id="relationshipDraftsGuide"', INDEX)
        self.assertIn('Choose the relationship step deliberately', INDEX)
        for expected in (
            'TXR-1507 · Short Form',
            'TXR-1501 · Long Form',
            'TXR-1508 · Showing Form',
            'TXR-1506 · Consumer Notice',
            'HomeOfferFlow does not select a form for you',
            'Drafts remain private until reviewed; where signing is enabled',
        ):
            self.assertIn(expected, INDEX)

    def test_lease_representation_starts_with_an_explicit_agent_selected_agreement_choice(self):
        self.assertIn("window.openTenantRepresentationDraft = function openTenantRepresentationDraft(kind)", INDEX)
        self.assertIn("Which brokerage-approved representation agreement are you preparing?", INDEX)
        self.assertIn("openTenantRepresentationDraft('short')", INDEX)
        self.assertIn("openTenantRepresentationDraft('long')", INDEX)
        self.assertIn("root.hofOpenTxr1507Draft = () => openDraftDialog(source);", INDEX)
        self.assertIn("root.hofOpenTxr1501Draft = () => openLongDraftDialog(source);", INDEX)
        self.assertIn("They do not infer which agreement is proper", INDEX)

    def test_public_agent_copy_matches_the_transaction_first_activation_path(self):
        self.assertIn('Start with the transaction—not a form catalog.', AGENTS)
        self.assertIn('Question 1', AGENTS)
        self.assertIn('What kind of transaction are you starting?', AGENTS)
        self.assertIn('Start question 1', AGENTS)
        self.assertNotIn('Start a buyer offer — no payment', AGENTS)
        self.assertIn('No password and no charge to start a private workspace.', AGENTS)
        self.assertIn('save your agent defaults afterward for faster repeat work', AGENTS)

    def test_agent_landing_preserves_the_safe_draft_request_through_sign_in(self):
        self.assertIn("hof_agent_landing_start_draft", INDEX)
        self.assertIn("const startAgentLandingDraft = localStorage.getItem('hof_agent_landing_start_draft') === '1';", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_start_draft', '1')", INDEX)
        self.assertIn("window.startAccountOffer?.();", INDEX)
        self.assertIn("agent_landing_draft_handoff", INDEX)

    def test_agent_workflow_guide_is_preserved_as_an_allowlisted_handoff_source(self):
        self.assertIn("const agentLandingSource = agentRouteParams.get('utm_source') === 'texas_agent_offer_workflow'", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_source', agentLandingSource)", INDEX)
        self.assertIn("localStorage.getItem('hof_agent_landing_source') === 'texas_agent_offer_workflow'", INDEX)
        self.assertIn("localStorage.removeItem('hof_agent_landing_source')", INDEX)
        self.assertIn("{ source: agentLandingSource, workflow: agentLandingWorkflow || 'purchase' }", INDEX)

    def test_public_endpoint_and_page_record_only_allowlisted_aggregate_agent_landing_events(self):
        self.assertIn("AGENT_LANDING_EVENT_TYPES", API)
        self.assertIn("def _record_agent_landing_event(data):", API)
        self.assertIn('"agent_landing_viewed": "viewed"', API)
        self.assertIn('"agent_landing_cta_selected": "selected"', API)
        self.assertIn('"agent_workflow_guide_viewed": "viewed"', API)
        self.assertIn('"agent_workflow_guide_cta_selected": "selected"', API)
        self.assertIn("AGENT_LANDING_CHANNELS", API)
        self.assertIn("AGENT_LANDING_CTA_PATHS", API)
        self.assertIn("Unsupported agent landing channel.", API)
        self.assertIn("Unsupported agent landing CTA path.", API)
        self.assertIn("CTA path is only allowed for agent CTA events.", API)
        self.assertIn('"channel": channel', API)
        self.assertIn("Unsupported agent landing event.", API)
        self.assertIn("'agent_landing_event'", API)
        self.assertIn('"surface": "agent_landing"', API)
        self.assertIn("data-agent-cta-path=\"client_draft\"", AGENTS)
        self.assertIn("data-agent-cta-path=\"seller_listing\"", AGENTS)
        self.assertIn("data-agent-cta-path=\"lease_listing\"", AGENTS)
        self.assertIn("data-agent-cta-path=\"lease_representation\"", AGENTS)
        self.assertIn("cta_path=ctaPath", AGENTS)
        self.assertIn("request_type:'agent_landing_event'", AGENTS)
        self.assertIn("agent_landing_viewed", AGENTS)
        self.assertIn("agent_landing_cta_selected", AGENTS)
        self.assertIn("new URLSearchParams(window.location.search).get('utm_source')", AGENTS)
        self.assertIn("'direct_outreach','email','social','referral','local_event','print'", AGENTS)
        self.assertIn("[data-agent-cta-path]", AGENTS)

    def test_agent_landing_channel_is_allowlisted_without_visitor_identity(self):
        spec = importlib.util.spec_from_file_location("agent_landing_channel", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = []
        with patch.object(api, "_record_partner_checkout_event", side_effect=lambda *args: captured.append(args)):
            api._record_agent_landing_event({"event_type": "agent_landing_cta_selected", "channel": "referral", "cta_path": "seller_listing"})
            with self.assertRaisesRegex(ValueError, "Unsupported agent landing channel"):
                api._record_agent_landing_event({"event_type": "agent_landing_viewed", "channel": "untrusted"})
            with self.assertRaisesRegex(ValueError, "Unsupported agent landing CTA path"):
                api._record_agent_landing_event({"event_type": "agent_landing_cta_selected", "channel": "referral", "cta_path": "untrusted"})
            with self.assertRaisesRegex(ValueError, "CTA path is only allowed"):
                api._record_agent_landing_event({"event_type": "agent_landing_viewed", "channel": "referral", "cta_path": "client_draft"})
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][0], "agent_landing_cta_selected")
        self.assertEqual(captured[0][3], {"surface": "agent_landing", "role": "agent", "channel": "referral", "ctaPath": "seller_listing"})

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
            'agentLandingCtaPathCounts', 'agentWorkflowGuideCtaPathCounts',
            'agentTransactionChoiceCounts',
            'agent_workflow_lease_representation_selected',
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
        self.assertIn("Landing CTA choices", INDEX)
        self.assertIn("Authenticated transaction choices", INDEX)
        self.assertIn("Guide CTA choices", INDEX)
        self.assertIn("agentLandingCtaPathCounts?.seller_listing", INDEX)
        self.assertIn("agentLandingCtaPathCounts?.lease_listing", INDEX)
        self.assertIn("agentLandingCtaPathCounts?.lease_representation", INDEX)
        self.assertIn("agentTransactionChoiceCounts?.lease_representation", INDEX)
        self.assertIn("agentWorkflowGuideCtaPathCounts?.relationship_drafts", INDEX)
        self.assertIn("agentWorkflowGuideCtaRate", INDEX)


if __name__ == "__main__":
    unittest.main()
