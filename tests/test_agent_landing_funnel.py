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
INVESTORS = (ROOT / "investors.html").read_text(encoding="utf-8")
FORM_LIBRARY = (ROOT / "texas-agent-form-library.html").read_text(encoding="utf-8")
VERCEL = (ROOT / "vercel.json").read_text(encoding="utf-8")


class AgentLandingFunnelTests(unittest.TestCase):
    def test_form_library_guide_measures_question_one_handoff_without_personal_data(self):
        self.assertIn('/assets/agent-workflow-guide-metrics.js', FORM_LIBRARY)
        self.assertLess(FORM_LIBRARY.index('/assets/agent-workflow-guide-metrics.js'), FORM_LIBRARY.index('</head>'))
        self.assertIn('href="/agents#transaction-start"', FORM_LIBRARY)
        self.assertIn('agent_workflow_guide_viewed', (ROOT / 'assets' / 'agent-workflow-guide-metrics.js').read_text(encoding='utf-8'))
        self.assertIn('form_library', (ROOT / 'assets' / 'agent-workflow-guide-metrics.js').read_text(encoding='utf-8'))

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
        self.assertIn('href="/?agent=1&amp;workflow=purchase&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector"', AGENTS)
        self.assertIn('href="/agents"', INDEX)
        self.assertIn("if (params().get('agent') === '1')", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('agent')", INDEX)
        self.assertIn("window.openAuthModal?.('agent')", INDEX)

    def test_public_agent_cta_routes_to_question_one_instead_of_assuming_a_buyer_offer(self):
        start = INDEX.index('function beginOfferFrom(surface)')
        end = INDEX.index('// Public landing pages', start)
        entry = INDEX[start:end]
        self.assertIn("(state?.data?.userType || 'homebuyer') === 'agent'", entry)
        target = "window.location.assign('/agents?utm_source=homeofferflow&utm_medium=homepage&utm_campaign=agent_workspace')"
        self.assertIn(target, entry)
        self.assertLess(entry.index(target), entry.index('startPrimaryOffer();'))
        self.assertIn("cta: 'Choose Your Transaction'", INDEX)

    def test_agent_landing_links_to_lease_workflow_guide(self):
        self.assertIn('href="/texas-lease-offer-workflow"', AGENTS)
        self.assertIn('Read the lease workflow guide', AGENTS)
        self.assertIn('data-agent-cta-path="lease_guide"', AGENTS)

    def test_agent_landing_links_to_listing_workflow_guide(self):
        self.assertIn('href="/texas-listing-workflow"', AGENTS)
        self.assertIn('Read the listing workflow guide', AGENTS)
        self.assertIn('data-agent-cta-path="listing_guide"', AGENTS)

    def test_agent_landing_uses_transaction_choices_for_guided_package_handoffs(self):
        self.assertIn('href="/?agent=1&amp;workflow=sale_listing&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector"', AGENTS)
        self.assertIn('href="/?agent=1&amp;workflow=lease_listing&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector"', AGENTS)
        self.assertIn("window.hofAgentWorkflowContext = agentLandingWorkflow", INDEX)
        self.assertIn("hof_agent_landing_package_workflow", INDEX)
        self.assertIn("agent_landing_package_handoff", INDEX)
        self.assertIn("window.hofOpenAgentPackageInterview?.(agentLandingWorkflow)", INDEX)

    def test_agent_landing_uses_the_neutral_listing_first_order(self):
        start = AGENTS.index('id="transaction-start"')
        end = AGENTS.index('</section>', start)
        choices = AGENTS[start:end]
        self.assertLess(choices.index('<h3>Listing</h3>'), choices.index('<h3>Buying</h3>'))
        self.assertLess(choices.index('<h3>Buying</h3>'), choices.index('<h3>Lease listing</h3>'))
        self.assertLess(choices.index('<h3>Lease listing</h3>'), choices.index('<h3>Lease representation</h3>'))

    def test_lease_listing_copy_does_not_claim_a_form_or_plan_is_preselected(self):
        self.assertIn("Next, choose lease-listing setup or lease details.", AGENTS)
        self.assertNotIn("with lease planning preselected.", AGENTS)

    def test_agent_landing_can_start_each_transaction_in_its_relevant_package_interview(self):
        for workflow, cta_path in (
            ("purchase", "client_draft"),
            ("sale_listing", "seller_listing"),
            ("lease_listing", "lease_listing"),
            ("lease_representation", "lease_representation"),
        ):
            self.assertIn(f'workflow={workflow}', AGENTS)
            self.assertIn(f'data-agent-cta-path="{cta_path}"', AGENTS)
        self.assertIn("const agentLandingWorkflow = ['purchase', 'sale_listing', 'lease_listing', 'lease_representation']", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_package_workflow', agentLandingWorkflow)", INDEX)
        self.assertIn("window.hofAgentWorkflowContext = agentLandingWorkflow", INDEX)
        self.assertIn("window.hofOpenAgentPackageInterview?.(agentLandingPackageWorkflow)", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('workflow')", INDEX)

    def test_agent_landing_uses_lease_representation_for_relationship_draft_handoffs(self):
        self.assertIn('href="/?agent=1&amp;workflow=lease_representation&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector"', AGENTS)
        self.assertIn("hof_agent_landing_open_relationship_workspace", INDEX)
        self.assertIn("agent_landing_relationship_workspace_handoff", INDEX)
        self.assertIn("tab: 'relationships'", INDEX)
        self.assertIn('id="accountPanelRelationships"', INDEX)
        self.assertIn("private TXR-1501, TXR-1506, TXR-1507, TXR-1508, TXR-1905, TXR-1914, TXR-1917, TXR-1919, TXR-1948, TXR-1953, and TXR-1954 review-draft creation for every signed-in agent", AGENTS)

    def test_transaction_question_one_uses_a_four_choice_responsive_grid(self):
        self.assertIn('class="skip-link" href="#transaction-start"', AGENTS)
        self.assertIn('.skip-link:focus', AGENTS)
        self.assertIn(".grid{display:grid;grid-template-columns:repeat(4,1fr)", AGENTS)
        self.assertIn("@media(max-width:960px){.grid{grid-template-columns:repeat(2,1fr)}}", AGENTS)
        self.assertIn("@media(max-width:760px){.grid{grid-template-columns:1fr}", AGENTS)
        self.assertIn("universal TREC-55-1 seller-disclosure and optional TREC-61-0 water-disclosure review drafts", AGENTS)

    def test_relationship_drafts_are_a_persistent_agent_account_workspace(self):
        self.assertIn('id="relationshipsAccountTab"', INDEX)
        self.assertIn('Agent Forms &amp; Drafts', INDEX)
        self.assertIn('data-account-tab="relationships"', INDEX)
        self.assertIn("onclick=\"showAccountTab('relationships')\"", INDEX)
        self.assertIn("normalized !== 'investor'", INDEX)
        self.assertIn("document.getElementById('accountPanelRelationships')", INDEX)
        self.assertIn("Prepare private relationship and consumer-notice drafts from the released shared library.", INDEX)

    def test_relationship_workspace_explains_each_private_draft_without_selecting_a_form(self):
        self.assertIn('id="relationshipDraftsGuide"', INDEX)
        self.assertIn('Choose the relationship step deliberately', INDEX)
        for expected in (
            'TXR-1507 · Short Form',
            'TXR-1501 · Long Form',
            'TXR-1508 · Showing Form',
            'TXR-1506 · Consumer Notice',
            'TXR-1914 · Seller Financing Addendum',
            'TXR-1917 · Environmental Assessment Addendum',
            'TXR-1919 · Loan Assumption Addendum',
            'HomeOfferFlow does not select a form for you',
            'Drafts remain private until reviewed; where signing is enabled',
        ):
            self.assertIn(expected, INDEX)

    def test_lease_representation_starts_with_an_explicit_agent_selected_agreement_choice(self):
        self.assertIn("window.openTenantRepresentationDraft = function openTenantRepresentationDraft(kind)", INDEX)
        self.assertIn("Which representation agreement are you preparing?", INDEX)
        self.assertIn("openTenantRepresentationDraft('short')", INDEX)
        self.assertIn("openTenantRepresentationDraft('long')", INDEX)
        self.assertIn("root.hofOpenTxr1507Draft = () => openDraftDialog(source);", INDEX)
        self.assertIn("root.hofOpenTxr1501Draft = () => openLongDraftDialog(source);", INDEX)
        self.assertIn("They do not infer which agreement is proper", INDEX)

    def test_lease_representation_lands_on_its_next_explicit_choice(self):
        self.assertIn("window.hofAgentWorkflowContext === 'lease_representation'", INDEX)
        self.assertIn("document.querySelector('#leaseRepresentationQuickChoices button')", INDEX)
        self.assertIn("firstChoice?.focus({ preventScroll: true });", INDEX)

    def test_public_agent_copy_matches_the_transaction_first_activation_path(self):
        self.assertIn('Start with the transaction—not a form catalog.', AGENTS)
        self.assertIn('Question 1', AGENTS)
        self.assertIn('Is this a listing, buying, lease listing, or lease representation transaction?', AGENTS)
        self.assertIn('Start question 1', AGENTS)
        self.assertIn('id="agentQuestionOneCta"', AGENTS)
        self.assertNotIn('Start a buyer offer — no payment', AGENTS)
        self.assertIn('No brokerage seat required.', AGENTS)
        self.assertIn("Every signed-in agent can use HomeOfferFlow's released shared form workflows.", AGENTS)
        self.assertIn('save your agent defaults afterward for faster repeat work', AGENTS)
        self.assertIn('OnDemand Realty agents:', AGENTS)
        self.assertIn('60 days free, then $29/month unless canceled.', AGENTS)
        self.assertIn('id="agentTrialOffer"', AGENTS)

    def test_buyer_offer_fixture_lease_handoff_points_agents_to_the_released_review_draft(self):
        self.assertIn('Lease-related purchase contracts use separate forms and are not included in the standard buyer packet.', INDEX)
        self.assertIn('TXR-1954 private review draft in the shared form library', INDEX)
        self.assertIn('utm_source=buyer_offer_interview&amp;utm_medium=lease_handoff&amp;utm_campaign=fixture_lease_review', INDEX)

    def test_ondemand_trial_links_preserve_agent_attribution(self):
        self.assertEqual(AGENTS.count('data-agent-cta-path="ondemand_trial"'), 2)
        self.assertEqual(AGENTS.count('utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=ondemand_trial'), 2)

    def test_agent_landing_metadata_targets_high_intent_real_estate_offer_searches(self):
        self.assertIn('<title>Texas Real Estate Offer Tools for Agents &amp; Brokers | HomeOfferFlow</title>', AGENTS)
        self.assertIn('Texas real estate offer tools for agents and brokers', AGENTS)
        self.assertIn('Texas real estate offer workflow software for agents and brokers', AGENTS)
        self.assertIn('Texas Real Estate Offer Tools for Agents &amp; Brokers | HomeOfferFlow', AGENTS)
        self.assertIn('"@type":"BreadcrumbList"', AGENTS)
        self.assertIn('"name":"Texas Agent and Broker Workspace"', AGENTS)

    def test_agent_faq_explains_the_question_two_package_interview_without_selecting_a_form(self):
        self.assertIn('What happens after I choose a transaction?', AGENTS)
        self.assertIn('<strong>Every choice</strong> opens one plain-language result question before a workflow is opened.', AGENTS)
        self.assertIn('<strong>Buying</strong> can lead to an offer, representation, or customer notice.', AGENTS)
        self.assertIn('<strong>Listing</strong> and <strong>lease listing</strong> can lead to the relevant listing, disclosure, or review work.', AGENTS)
        self.assertIn('<strong>Lease representation</strong> can lead to representation or customer-notice work.', AGENTS)
        self.assertIn('HomeOfferFlow does not automatically select a legal form.', AGENTS)

    def test_agent_landing_cards_and_structured_data_match_the_question_two_interview(self):
        self.assertIn('Question 2 asks the result you need, then opens only the matching guided workflow.', AGENTS)
        self.assertIn('Next, choose an offer, representation, or a customer notice.', AGENTS)
        self.assertIn('Every transaction choice opens one plain-language result question before a workflow is opened.', AGENTS)

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
        self.assertIn('"agent_landing_question_one_viewed": "question_one_viewed"', API)
        self.assertIn('"agent_landing_question_one_opened": "opened"', API)
        self.assertIn('"agent_landing_cta_selected": "selected"', API)
        self.assertIn('"agent_workflow_guide_viewed": "viewed"', API)
        self.assertIn('"agent_workflow_guide_cta_selected": "selected"', API)
        self.assertIn('"agent_resource_links_expanded": "resource_expanded"', API)
        self.assertIn("AGENT_LANDING_CHANNELS", API)
        self.assertIn("AGENT_LANDING_CTA_PATHS", API)
        self.assertIn('"listing_guide"', API)
        self.assertIn('"lease_guide"', API)
        self.assertIn('"form_library_guide"', API)
        self.assertIn('form_library_guide', ADMIN)
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
        self.assertIn("agent_landing_question_one_viewed", AGENTS)
        self.assertIn("agent_landing_question_one_opened", AGENTS)
        self.assertIn("agentQuestionOneCta", AGENTS)
        self.assertIn("agent_landing_cta_selected", AGENTS)
        self.assertIn("utm_source=agent_workspace", INDEX)
        self.assertIn("window.location.pathname === '/agents'", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertIn("utm_medium=agent_page", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertIn("hofAgentFormLibraryCta", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertIn("See the shared form library", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertIn("const params=new URLSearchParams(window.location.search)", AGENTS)
        self.assertIn("'direct_outreach','email','social','referral','local_event','print'", AGENTS)
        self.assertIn("[data-agent-cta-path]", AGENTS)

    def test_agent_landing_channel_is_allowlisted_without_visitor_identity(self):
        spec = importlib.util.spec_from_file_location("agent_landing_channel", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = []
        with patch.object(api, "_record_partner_checkout_event", side_effect=lambda *args: captured.append(args)):
            api._record_agent_landing_event({"event_type": "agent_landing_cta_selected", "channel": "referral", "cta_path": "seller_listing"})
            api._record_agent_landing_event({"event_type": "agent_landing_cta_selected", "channel": "referral", "cta_path": "listing_guide"})
            api._record_agent_landing_event({"event_type": "agent_landing_cta_selected", "channel": "referral", "cta_path": "lease_guide"})
            api._record_agent_landing_event({"event_type": "agent_landing_question_one_opened", "channel": "referral"})
            api._record_agent_landing_event({"event_type": "agent_landing_question_one_viewed", "channel": "referral"})
            with self.assertRaisesRegex(ValueError, "Unsupported agent landing channel"):
                api._record_agent_landing_event({"event_type": "agent_landing_viewed", "channel": "untrusted"})
            with self.assertRaisesRegex(ValueError, "Unsupported agent landing CTA path"):
                api._record_agent_landing_event({"event_type": "agent_landing_cta_selected", "channel": "referral", "cta_path": "untrusted"})
            with self.assertRaisesRegex(ValueError, "CTA path is only allowed"):
                api._record_agent_landing_event({"event_type": "agent_landing_viewed", "channel": "referral", "cta_path": "client_draft"})
        self.assertEqual(len(captured), 5)
        self.assertEqual(captured[0][0], "agent_landing_cta_selected")
        self.assertEqual(captured[0][3], {"surface": "agent_landing", "role": "agent", "channel": "referral", "ctaPath": "seller_listing"})
        self.assertEqual(captured[1][3]["ctaPath"], "listing_guide")
        self.assertEqual(captured[2][3]["ctaPath"], "lease_guide")
        self.assertEqual(captured[3][0], "agent_landing_question_one_opened")
        self.assertEqual(captured[3][3], {"surface": "agent_landing", "role": "agent", "channel": "referral"})
        self.assertEqual(captured[4][0], "agent_landing_question_one_viewed")
        self.assertEqual(captured[4][3], {"surface": "agent_landing", "role": "agent", "channel": "referral"})

    def test_agent_transaction_selector_campaign_is_allowlisted_and_aggregate_only(self):
        spec = importlib.util.spec_from_file_location("agent_landing_campaign", API_PATH)
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        captured = []
        with patch.object(api, "_record_partner_checkout_event", side_effect=lambda *args: captured.append(args)):
            api._record_agent_landing_event({
                "event_type": "agent_landing_cta_selected",
                "channel": "unspecified",
                "cta_path": "client_draft",
                "utm_campaign": "transaction_selector",
            })
            with self.assertRaisesRegex(ValueError, "Unsupported agent landing campaign"):
                api._record_agent_landing_event({
                    "event_type": "agent_landing_cta_selected",
                    "channel": "unspecified",
                    "cta_path": "client_draft",
                    "utm_campaign": "untrusted_campaign",
                })
        self.assertEqual(captured[0][3], {
            "surface": "agent_landing",
            "role": "agent",
            "channel": "unspecified",
            "ctaPath": "client_draft",
            "utmCampaign": "transaction_selector",
        })

    def test_public_agent_landing_preserves_organic_and_pwa_attribution(self):
        self.assertIn("medium==='installed_app'||source==='pwa_shortcut'?'pwa_shortcut'", AGENTS)
        self.assertIn("medium==='organic_content'||source==='organic'?'organic'", AGENTS)
        self.assertIn("body?.request_type==='agent_landing_event'", AGENTS)

    def test_transaction_selection_uses_beacon_delivery_before_navigation(self):
        self.assertIn("navigator.sendBeacon('/api/fsbo-lead',new Blob([payload],{type:'application/json'}))", AGENTS)
        self.assertIn("keepalive:true,body:payload", AGENTS)

    def test_transaction_choices_carry_a_shared_campaign_into_the_agent_workspace(self):
        self.assertEqual(AGENTS.count('utm_campaign=transaction_selector'), 4)
        self.assertIn('workflow=sale_listing&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector', AGENTS)
        self.assertIn('workflow=purchase&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector', AGENTS)
        self.assertIn('workflow=lease_listing&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector', AGENTS)
        self.assertIn('workflow=lease_representation&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector', AGENTS)
        self.assertIn("const transactionPaths=new Set(['client_draft','seller_listing','lease_listing','lease_representation'])", AGENTS)
        self.assertIn("body.utm_campaign=campaign", AGENTS)
        self.assertIn('"agentLandingCtaRatesByCampaign"', ADMIN)
        self.assertIn('Agent campaign conversion:', INDEX)

    def test_investor_landing_preserves_organic_and_pwa_attribution(self):
        self.assertIn("medium==='installed_app'||source==='pwa_shortcut'?'pwa_shortcut'", INVESTORS)
        self.assertIn("medium==='organic_content'||source==='organic'?'organic'", INVESTORS)

    def test_admin_reports_agent_workspace_landing_conversion(self):
        for expected in (
            '"agentLandingViewCount"', '"agentLandingQuestionOneViewCount"', '"agentLandingQuestionOneViewRate"', '"agentLandingQuestionOneOpenCount"', '"agentLandingQuestionOneOpenRate"', '"agentLandingCtaCount"', '"agentLandingCtaRate"',
            '"agentLandingViewCountsByChannel"', '"agentLandingCtaCountsByChannel"',
            '"agentLandingCtaRatesByChannel"',
            '"agentResourceLinksExpandedCount"',
            '"agentLandingDraftHandoffUserCount"', '"agentLandingDraftHandoffRate"',
            '"agentLandingSellerWorkspaceHandoffUserCount"',
            '"agentLandingRelationshipWorkspaceHandoffUserCount"',
            'agent_landing_draft_handoff',
            'agent_landing_seller_workspace_handoff',
            'agent_landing_relationship_workspace_handoff',
            'agentWorkflowGuideViewCount', 'agentWorkflowGuideCtaCount', 'agentWorkflowGuideCtaRate',
            'agentLandingCtaPathCounts', 'agentWorkflowGuideCtaPathCounts',
            'agentTransactionChoiceCounts',
            'agentWorkflowResumeCount',
            'agentFormPackageInterviewViewCount', 'agentFormPackageSelectionCount', 'agentFormPackageSelectionRate',
            'agentFormPackageInterviewCountsByWorkflow', 'agentFormPackageSelectionCountsByWorkflow',
            'agent_workflow_lease_representation_selected',
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("Agent Workspace Funnel", INDEX)
        self.assertIn("agentLandingCtaRate", INDEX)
        self.assertIn("agentLandingQuestionOneViewRate", INDEX)
        self.assertIn("agentLandingQuestionOneOpenRate", INDEX)
        self.assertIn("Channel views / sign-ins", INDEX)
        self.assertIn("Agent channel conversion:", INDEX)
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
        self.assertIn("agentWorkflowResumeCount", INDEX)
        self.assertIn("agentFormPackageSelectionRate", INDEX)
        self.assertIn("agentFormPackageSelectionCountsByWorkflow?.lease_representation", INDEX)
        self.assertIn("agentWorkflowGuideCtaPathCounts?.relationship_drafts", INDEX)
        self.assertIn("agentWorkflowGuideCtaRate", INDEX)

    def test_question_two_conversion_excludes_pre_instrumentation_selections(self):
        self.assertIn("agent_form_package_interview_started_at", ADMIN)
        self.assertIn("agent_form_package_selection_events", ADMIN)
        self.assertIn("created_at >= first_view_at", ADMIN)

    def test_homepage_offer_entry_events_keep_anonymous_campaign_source(self):
        self.assertIn("const entrySource = String(new URLSearchParams(window.location.search).get('utm_source') || 'homepage')", INDEX)
        self.assertIn("source: entrySource", INDEX)


if __name__ == "__main__":
    unittest.main()
