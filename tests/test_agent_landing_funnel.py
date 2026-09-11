from pathlib import Path
import importlib.util
import shutil
import subprocess
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
    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for lease-listing handoff runtime tests')
    def test_lease_listing_records_a_real_workspace_start_after_the_address_question_loads(self):
        result = subprocess.run(
            ['node', '--test', str(ROOT / 'tests' / 'agent_lease_listing_handoff.runtime.cjs')],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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

    def test_returning_agent_has_a_clear_workspace_sign_in_without_preselecting_a_transaction(self):
        self.assertIn('class="workspace-sign-in" href="/?agent=1&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=returning_workspace">Sign in</a>', AGENTS)
        self.assertIn('.workspace-sign-in:focus-visible', AGENTS)
        self.assertNotIn('workflow=', AGENTS[AGENTS.index('class="workspace-sign-in"'):AGENTS.index('</a>', AGENTS.index('class="workspace-sign-in"'))])

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
        self.assertIn("const selectedType = selectedLandingAudience();", entry)
        self.assertIn("selectedType === 'agent'", entry)
        target = "window.location.assign('/agents?utm_source=homeofferflow&utm_medium=homepage&utm_campaign=agent_workspace')"
        self.assertIn(target, entry)
        self.assertLess(entry.index(target), entry.index('startHomebuyerOffer();'))
        self.assertIn("cta: 'Start a Transaction'", INDEX)

    def test_homepage_agent_entry_has_its_own_privacy_safe_conversion_channel(self):
        self.assertIn('"homepage"', API)
        self.assertIn("source==='homeofferflow'||medium==='homepage'?'homepage'", AGENTS)
        focus = (ROOT / 'assets' / 'agent-landing-focus.js').read_text(encoding='utf-8')
        self.assertIn("'homepage'", focus)
        self.assertNotIn("agent_email", AGENTS)
        self.assertNotIn("client_email", AGENTS)

    def test_agent_landing_keeps_reference_guides_out_of_the_first_screen(self):
        hero = AGENTS.split('<section class="grid" id="transaction-start"', 1)[0]
        self.assertNotIn('form_library_guide', hero)
        self.assertNotIn('listing_guide', hero)
        self.assertNotIn('lease_guide', hero)
        self.assertLess(AGENTS.index('id="transaction-start"'), AGENTS.index('Start your 60-day trial'))

    def test_agent_landing_uses_transaction_choices_for_guided_package_handoffs(self):
        self.assertIn('href="/?agent=1&amp;workflow=sale_listing&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector"', AGENTS)
        self.assertIn('href="/?agent=1&amp;workflow=lease_listing&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector"', AGENTS)
        self.assertIn("window.startAgentWorkflow?.(agentLandingWorkflow)", INDEX)
        self.assertIn("hof_agent_landing_package_workflow", INDEX)
        self.assertIn("agent_landing_package_handoff", INDEX)
        self.assertIn("window.startAgentWorkflow?.(agentLandingPackageWorkflow)", INDEX)

    def test_agent_sign_in_confirms_the_selected_transaction_will_continue(self):
        start = INDEX.index("if (params().get('agent') === '1')")
        end = INDEX.index("// Investor acquisition", start)
        entry = INDEX[start:end]
        self.assertIn("const workflowLabel = {", entry)
        self.assertIn("sale_listing: 'property listing'", entry)
        self.assertIn("lease_listing: 'lease listing'", entry)
        self.assertIn("lease_representation: 'tenant representation transaction'", entry)
        self.assertIn("Continue to your ${workflowLabel}", entry)
        self.assertIn("We’ll open the next questions for this ${workflowLabel} after you return.", entry)

    def test_agent_sign_in_role_copy_covers_listing_lease_and_purchase_work(self):
        self.assertIn("<span>Personal transaction workspace</span>", INDEX)
        self.assertNotIn("<span>Personal offer workspace</span>", INDEX)

    def test_agent_deep_link_waits_for_existing_session_resolution(self):
        start = INDEX.index("const continueAfterAuthResolution = callback =>")
        end = INDEX.index("// Investor acquisition", start)
        entry = INDEX[start:end]
        self.assertIn("window.__hofDraftRestoreAuthReady", entry)
        self.assertIn("window.addEventListener('hof-auth-ready', callback, { once: true });", entry)
        self.assertIn("continueAfterAuthResolution(() => {", entry)

    def test_signed_in_agent_deep_link_waits_for_the_account_workspace_before_opening_the_transaction(self):
        start = INDEX.index("if (window.hofAuth?.session) {", INDEX.index("// Agent acquisition reuses"))
        end = INDEX.index("} else if (agentLandingWorkspace === 'seller')", start)
        signed_in = INDEX[start:end]
        self.assertIn("const accountDashboard = window.openAccountDashboard?.({ tab: 'dashboard' });", signed_in)
        self.assertIn("typeof accountDashboard.then === 'function'", signed_in)
        self.assertIn("Promise.resolve(accountDashboard).then(continueToSelectedTransaction, continueToSelectedTransaction);", signed_in)
        self.assertIn("window.startAgentWorkflow?.(agentLandingWorkflow);", signed_in)
        self.assertNotIn("}, 120);", signed_in)

    def test_agent_deep_link_recovers_if_the_ready_event_precedes_the_dom_handler(self):
        self.assertIn('id="hof-agent-route-primer-v1"', INDEX)
        self.assertIn("'hof_agent_route_pending_v1'", INDEX)
        self.assertIn('id="hof-agent-landing-route-recovery-v1"', INDEX)
        self.assertIn("window.__hofAgentLandingRouteProcessed = true;", INDEX)
        start = INDEX.index('id="hof-agent-landing-route-recovery-v1"')
        end = INDEX.index('</script>', start)
        recovery = INDEX[start:end]
        self.assertIn("if (!window.__hofDraftRestoreAuthReady)", recovery)
        self.assertIn('window.setTimeout(continueAgentLandingRoute, 200);', recovery)
        self.assertIn("window.openAuthModal?.('agent');", recovery)
        self.assertIn("window.startAgentWorkflow?.(workflow);", recovery)
        self.assertIn("['agent', 'workflow', 'workspace']", recovery)
        self.assertIn("sessionStorage.getItem('hof_agent_route_pending_v1')", recovery)
        self.assertIn("localStorage.getItem('hof_agent_route_pending_v1')", recovery)

    def test_agent_route_recovery_waits_for_the_workspace_before_opening_the_transaction(self):
        start = INDEX.index("if (window.hofAuth?.session) {", INDEX.index('id="hof-agent-landing-route-recovery-v1"'))
        end = INDEX.index("try {\n      if (source", start)
        signed_in = INDEX[start:end]
        self.assertIn("const accountDashboard = window.openAccountDashboard?.({ tab: workspace === 'seller'", signed_in)
        self.assertIn("typeof accountDashboard.then === 'function'", signed_in)
        self.assertIn("Promise.resolve(accountDashboard).then(continueToSelectedTransaction, continueToSelectedTransaction);", signed_in)
        self.assertIn("window.startAgentWorkflow?.(workflow);", signed_in)
        self.assertNotIn("}, 120);", signed_in)

    def test_agent_deep_link_shows_agent_landing_before_session_restores(self):
        start = INDEX.index("if (params().get('agent') === '1')")
        end = INDEX.index("// Investor acquisition", start)
        entry = INDEX[start:end]
        self.assertIn("window.setAudience?.('agent');", entry)
        self.assertIn("const initialAgentLandingWorkflow", entry)
        self.assertLess(entry.index("const initialAgentLandingWorkflow"), entry.index("setTimeout(() => continueAfterAuthResolution"))
        self.assertLess(entry.index("window.setAudience?.('agent');"), entry.index("setTimeout(() => continueAfterAuthResolution"))

    def test_package_start_telemetry_waits_for_the_destination_workspace(self):
        start = INDEX.index("window.hofOpenAgentPackageInterview = function")
        end = INDEX.index("window.startAgentWorkflow = function", start)
        interview = INDEX[start:end]
        self.assertIn("const recordPackageWorkspaceStart = (choice)", interview)
        self.assertIn("choice.isWorkspaceOpen?.()", interview)
        self.assertIn("recordPackageWorkspaceStart(choice);", interview)
        self.assertIn("document.getElementById('wizardOverlay')?.classList.contains('active')", interview)
        self.assertIn("document.getElementById('listingWorkspaceStartCard')", interview)
        self.assertIn("document.getElementById('hofAgentPackageFollowUp')", interview)
        self.assertEqual(interview.count("if (attempts < 100)"), 2)
        self.assertIn("undercounting a real start", interview)

    def test_package_interview_makes_the_review_before_send_boundary_plain(self):
        start = INDEX.index("window.hofOpenAgentPackageInterview = function")
        end = INDEX.index("window.startAgentWorkflow = function", start)
        interview = INDEX[start:end]
        self.assertIn(
            "Choose one task. We’ll guide you through only the questions and documents it requires.",
            interview,
        )
        self.assertNotIn("then send it when the parties are ready", interview)

    def test_agent_landing_uses_the_neutral_listing_first_order(self):
        start = AGENTS.index('id="transaction-start"')
        end = AGENTS.index('</section>', start)
        choices = AGENTS[start:end]
        self.assertLess(choices.index('<h3>Property listing</h3>'), choices.index('<h3>Purchase</h3>'))
        self.assertLess(choices.index('<h3>Purchase</h3>'), choices.index('<h3>Lease listing</h3>'))
        self.assertLess(choices.index('<h3>Lease listing</h3>'), choices.index('<h3>Tenant representation</h3>'))

    def test_agent_landing_uses_document_review_language_for_customers(self):
        self.assertIn('"name":"Review your documents"', AGENTS)
        self.assertIn('document summary, form status, recipients', AGENTS)
        self.assertIn('Save your agent details once for faster repeat work', AGENTS)
        self.assertNotIn('"name":"Review the draft"', AGENTS)
        self.assertNotIn('saved defaults, draft recovery, repeat-offer work', AGENTS)

    def test_lease_listing_copy_routes_to_landlord_work_instead_of_purchase_addenda(self):
        self.assertIn("Add the landlord and property details to begin.", AGENTS)
        self.assertNotIn("Next, choose listing setup, a lease addendum, or your saved workspace.", AGENTS)
        self.assertNotIn("Next, choose listing setup, request a lease form, or open your saved workspace.", AGENTS)
        self.assertNotIn("Next, choose lease-listing setup or lease details.", AGENTS)
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
        self.assertIn("Continue to your ${workflowLabel}", INDEX)
        self.assertIn("window.startAgentWorkflow?.(agentLandingWorkflow)", INDEX)
        self.assertIn("window.startAgentWorkflow?.(agentLandingPackageWorkflow)", INDEX)
        self.assertIn("cleanUrl.searchParams.delete('workflow')", INDEX)

    def test_agent_landing_uses_lease_representation_for_relationship_draft_handoffs(self):
        self.assertIn('href="/?agent=1&amp;workflow=lease_representation&amp;utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=transaction_selector"', AGENTS)
        self.assertIn("hof_agent_landing_open_relationship_workspace", INDEX)
        self.assertIn("agent_landing_relationship_workspace_handoff", INDEX)
        self.assertIn("tab: 'relationships'", INDEX)
        self.assertIn('id="accountPanelRelationships"', INDEX)
        self.assertIn("Every signed-in agent can use HomeOfferFlow's released shared forms", AGENTS)
        self.assertIn("the interview keeps the relevant documents together for the transaction", AGENTS)

    def test_transaction_question_one_uses_a_four_choice_responsive_grid(self):
        self.assertIn('class="skip-link" href="#transaction-start"', AGENTS)
        self.assertIn('.skip-link:focus', AGENTS)
        self.assertIn(".grid{display:grid;grid-template-columns:repeat(4,1fr)", AGENTS)
        self.assertIn("@media(max-width:960px){.grid{grid-template-columns:repeat(2,1fr)}}", AGENTS)
        self.assertIn("@media(max-width:760px){.grid{grid-template-columns:1fr}", AGENTS)
        self.assertIn("Start a transaction, then prepare only what it needs.", AGENTS)
        self.assertIn("What you can do here", AGENTS)
        self.assertNotIn("Current launch scope", AGENTS)

    def test_relationship_drafts_are_a_persistent_agent_account_workspace(self):
        self.assertIn('id="relationshipsAccountTab"', INDEX)
        self.assertIn('Guided Forms', INDEX)
        self.assertIn('data-account-tab="relationships"', INDEX)
        self.assertIn("onclick=\"showAccountTab('relationships')\"", INDEX)
        self.assertIn("normalized !== 'investor'", INDEX)
        self.assertIn("document.getElementById('accountPanelRelationships')", INDEX)
        self.assertIn("Start with what your client needs. We’ll guide you to the right document interview", INDEX)

    def test_relationship_workspace_explains_each_private_draft_without_selecting_a_form(self):
        self.assertIn('id="relationshipDraftsGuide"', INDEX)
        self.assertIn('Start with the client need', INDEX)
        for expected in (
            'Straightforward representation agreement · TXR-1507',
            'Detailed representation agreement · TXR-1501',
            'Unrepresented-customer showing form · TXR-1508',
            'TXR-1506 · Consumer Notice',
            'TXR-1914 · Seller Financing Addendum',
            'TXR-1917 · Environmental Assessment Addendum',
            'TXR-1919 · Loan Assumption Addendum',
            'Start with what your client needs',
            'then you review the completed document before sending it for signature.',
        ):
            self.assertIn(expected, INDEX)

    def test_lease_representation_starts_with_an_explicit_agent_selected_agreement_choice(self):
        self.assertIn("window.openTenantRepresentationDraft = function openTenantRepresentationDraft(kind)", INDEX)
        self.assertIn("What kind of representation does this client need?", INDEX)
        self.assertIn("openTenantRepresentationDraft('short')", INDEX)
        self.assertIn("openTenantRepresentationDraft('long')", INDEX)
        self.assertIn("root.hofOpenTxr1507Draft = () => openDraftDialog(source);", INDEX)
        self.assertIn("root.hofOpenTxr1501Draft = () => openLongDraftDialog(source);", INDEX)
        self.assertIn("They do not infer which agreement is proper", INDEX)

    def test_purchase_interview_keeps_common_addenda_in_the_guided_handoff(self):
        start = INDEX.index("window.hofOpenAgentPackageInterview = function")
        end = INDEX.index("window.startAgentWorkflow = function", start)
        interview = INDEX[start:end]
        self.assertIn("Prepare a purchase addendum", interview)
        self.assertIn("Which purchase addendum does this transaction need?", interview)
        for label, opener in (
            ("Seller financing", "hofOpenTxr1914Draft"),
            ("Loan assumption", "hofOpenTxr1919Draft"),
            ("Environmental review", "hofOpenTxr1917Draft"),
            ("Appraisal review", "hofOpenTxr1948Draft"),
            ("Residential lease addendum", "hofOpenTxr1953Draft"),
            ("Fixture lease addendum", "hofOpenTxr1954Draft"),
            ("Mineral reservation", "hofOpenTxr1905Draft"),
        ):
            self.assertIn(label, interview)
            self.assertIn(opener, interview)
        self.assertIn("hof-purchase-addendum-interview-openers-v1", INDEX)
        self.assertIn("openExistingPrivateDraft", INDEX)

    def test_lease_listing_does_not_offer_purchase_contract_lease_addenda(self):
        start = INDEX.index("lease_listing: {")
        end = INDEX.index("lease_representation: {", start)
        lease_listing = INDEX[start:end]
        self.assertIn("Next, add the landlord and property details for this lease listing.", lease_listing)
        self.assertIn("showAccountTab('seller');", lease_listing)
        self.assertIn("document.getElementById('listingWorkspaceAddress')", lease_listing)
        self.assertIn("agent_form_package_started", lease_listing)
        self.assertIn("workflow: 'lease_listing'", lease_listing)
        self.assertIn("package: 'Lease listing workspace'", lease_listing)
        self.assertNotIn("hofOpenAgentPackageInterview('lease_listing')", lease_listing)
        self.assertNotIn("openRelationshipPackage('lease_addendum')", lease_listing)
        self.assertNotIn("openRelationshipPackage('purchase_addendum')", lease_listing)
        self.assertNotIn("hofOpenTxr1953Draft", lease_listing)
        self.assertNotIn("hofOpenTxr1954Draft", lease_listing)

    def test_guided_private_draft_handoff_offers_a_prefilled_missing_form_request(self):
        start = INDEX.index("const openRelationshipDraft = (openerName, onOpened, request)")
        end = INDEX.index("const openRelationshipPackage = (type)", start)
        handoff = INDEX[start:end]
        self.assertIn("const reportOpenError", handoff)
        self.assertIn("Promise.resolve().then(() => opener()).then(() => {", handoff)
        self.assertIn("document.getElementById('hofAgentDocumentOpenStatus')", handoff)
        self.assertIn("retryButton.textContent = 'Try again';", handoff)
        self.assertIn("We couldn’t open that document. Please try again.", handoff)
        self.assertIn("Get help with this document", handoff)
        self.assertIn("window.openMissingFormRequest({", handoff)
        self.assertIn("formName: request.formCode || request.label", handoff)
        self.assertIn("transaction: transactionLabels[kind] || 'Other Texas transaction'", handoff)

    def test_nested_package_start_waits_for_the_actual_private_draft_dialog(self):
        start = INDEX.index("window.hofOpenAgentPackageInterview = function")
        end = INDEX.index("window.startAgentWorkflow = function", start)
        interview = INDEX[start:end]
        self.assertIn("const recordPrivateDraftWorkspaceStart = (choice, packageType)", interview)
        self.assertIn("document.querySelector('.hof-agreement-dialog')", interview)
        self.assertIn("deferStartToNestedChoice: true", interview)
        self.assertIn("if (!choice.deferStartToNestedChoice && !choice.skipWorkspaceStart) recordPackageWorkspaceStart(choice);", interview)
        self.assertIn("openRelationshipDraft(choice.opener, () => recordPrivateDraftWorkspaceStart(choice, type), choice);", interview)

    def test_missing_form_request_prefills_the_selected_form_and_transaction(self):
        start = INDEX.index("function openMissingFormRequest(context = {})")
        end = INDEX.index("function isAgentAccount()", start)
        request = INDEX[start:end]
        self.assertIn("if (transaction && context.transaction) transaction.value = context.transaction;", request)
        self.assertIn("if (formName && context.formName) formName.value = context.formName;", request)
        self.assertIn("formName?.focus();", request)

    def test_nested_relationship_choice_returns_to_the_prior_package_question(self):
        start = INDEX.index("window.hofOpenAgentPackageInterview = function")
        end = INDEX.index("window.startAgentWorkflow = function", start)
        interview = INDEX[start:end]
        self.assertIn("const returnToPackageQuestion = () =>", interview)
        self.assertIn("window.hofOpenAgentPackageInterview?.(kind);", interview)
        self.assertIn("addEventListener('click', returnToPackageQuestion)", interview)

    def test_package_copy_explains_review_before_available_signing(self):
        start = INDEX.index("window.hofOpenAgentPackageInterview = function")
        end = INDEX.index("window.startAgentWorkflow = function", start)
        interview = INDEX[start:end]
        self.assertIn("Choose one task. We’ll guide you through only the questions and documents it requires.", interview)
        self.assertIn("You’ll review the completed document before sending it for signature.", interview)
        self.assertIn("For a purchase involving existing tenant leases.", interview)
        self.assertIn("For a purchase involving leased fixtures, such as solar panels.", interview)

    def test_dismissing_the_package_question_restores_keyboard_focus(self):
        start = INDEX.index("window.hofOpenAgentPackageInterview = function")
        end = INDEX.index("window.startAgentWorkflow = function", start)
        interview = INDEX[start:end]
        self.assertIn("const returnFocus = document.activeElement instanceof HTMLElement", interview)
        self.assertIn("const closeInterview = (reason = 'dismissed') =>", interview)
        self.assertIn("returnFocus?.focus({ preventScroll: true });", interview)
        self.assertIn("addEventListener('click', () => closeInterview('back'))", interview)
        self.assertIn("addEventListener('click', event => { if (event.target === modal) closeInterview('overlay'); });", interview)

    def test_lease_representation_lands_on_its_next_explicit_choice(self):
        self.assertIn("window.hofAgentWorkflowContext === 'lease_representation'", INDEX)
        self.assertIn("document.querySelector('#leaseRepresentationQuickChoices button')", INDEX)
        self.assertIn("firstChoice?.focus({ preventScroll: true });", INDEX)

    def test_public_agent_copy_matches_the_transaction_first_activation_path(self):
        self.assertIn('Start with the transaction—not a form catalog.', AGENTS)
        self.assertIn('Question 1', AGENTS)
        self.assertIn('What type of transaction are you starting?', AGENTS)
        self.assertIn('Property listing', AGENTS)
        self.assertIn('Purchase', AGENTS)
        self.assertIn('Tenant representation', AGENTS)
        self.assertNotIn('Start question 1', AGENTS)
        self.assertNotIn('id="agentQuestionOneCta"', AGENTS)
        self.assertNotIn('Start a buyer offer — no payment', AGENTS)
        self.assertIn('No brokerage seat required.', AGENTS)
        self.assertIn("Every signed-in agent can use HomeOfferFlow's released shared forms and create a listing workspace.", AGENTS)
        self.assertNotIn('agent-owned private listing workspace', AGENTS)
        self.assertIn('You do not need a brokerage seat to create your own seller or lease-listing workspace.', AGENTS)
        self.assertIn('save your defaults for faster repeat work', AGENTS)
        self.assertIn('OnDemand Realty agents:', AGENTS)
        self.assertIn('60 days free, then $29/month unless canceled.', AGENTS)
        self.assertIn('id="agentTrialOffer"', AGENTS)

    def test_buyer_offer_fixture_lease_stays_in_the_package_interview(self):
        self.assertIn('HomeOfferFlow will include the right addendum', INDEX)
        self.assertIn('id="fixtureLeaseInterview"', INDEX)
        self.assertIn('The completed lease addendum will be placed in this offer package automatically.', INDEX)
        step_start = INDEX.index('<div class="wizard-step" id="step2">')
        step_end = INDEX.index('<div class="wizard-step" id="step3">', step_start)
        self.assertNotIn('utm_medium=lease_handoff', INDEX[step_start:step_end])

    def test_ondemand_trial_links_preserve_agent_attribution(self):
        self.assertEqual(AGENTS.count('data-agent-cta-path="ondemand_trial"'), 1)
        self.assertEqual(AGENTS.count('utm_source=agent_workspace&amp;utm_medium=agent_page&amp;utm_campaign=ondemand_trial'), 1)

    def test_agent_landing_metadata_targets_high_intent_real_estate_offer_searches(self):
        self.assertIn('<title>Texas Real Estate Offer Tools for Agents &amp; Brokers | HomeOfferFlow</title>', AGENTS)
        self.assertIn('Texas real estate offer tools for agents and brokers', AGENTS)
        self.assertIn('Texas real estate offer workflow software for agents and brokers', AGENTS)
        self.assertIn('Texas Real Estate Offer Tools for Agents &amp; Brokers | HomeOfferFlow', AGENTS)
        self.assertIn('"@type":"BreadcrumbList"', AGENTS)
        self.assertIn('"name":"Texas Agent and Broker Workspace"', AGENTS)

    def test_agent_faq_explains_the_transaction_specific_next_step(self):
        self.assertIn('What happens after I choose a transaction?', AGENTS)
        self.assertIn('<strong>Purchase</strong> lets you choose a purchase offer, buyer representation agreement, addendum, or customer showing form.', AGENTS)
        self.assertIn('<strong>Property listing</strong> lets you choose a listing task, seller disclosure, or buyer-offer comparison.', AGENTS)
        self.assertIn('<strong>Lease listing</strong> goes directly to the landlord and property details.', AGENTS)
        self.assertIn('<strong>Tenant representation</strong> lets you choose a tenant representation agreement or customer showing form.', AGENTS)
        self.assertIn('The interview then asks only for the details that apply.', AGENTS)

    def test_agent_landing_cards_and_structured_data_match_the_question_two_interview(self):
        self.assertIn('Choose the transaction type. We’ll take you to the next question or detail that applies.', AGENTS)
        self.assertIn('Choose a purchase offer, buyer representation agreement, addendum, or showing form.', AGENTS)
        self.assertIn('Lease listing goes directly to the landlord and property details.', AGENTS)

    def test_generic_agent_landing_preserves_the_transaction_choice_through_sign_in(self):
        self.assertIn("hof_agent_landing_start_draft", INDEX)
        self.assertIn("const startAgentLandingDraft = localStorage.getItem('hof_agent_landing_start_draft') === '1';", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_start_draft', '1')", INDEX)
        self.assertIn("window.openAgentTransactionPicker?.();", INDEX)
        self.assertIn("window.openAccountDashboard?.({ tab: 'dashboard' });", INDEX)
        self.assertIn("agent_landing_draft_handoff", INDEX)

    def test_agent_workflow_guide_is_preserved_as_an_allowlisted_handoff_source(self):
        self.assertIn("const agentLandingSource = agentRouteParams.get('utm_source') === 'texas_agent_offer_workflow'", INDEX)
        self.assertIn("localStorage.setItem('hof_agent_landing_source', agentLandingSource)", INDEX)
        self.assertIn("localStorage.getItem('hof_agent_landing_source') === 'texas_agent_offer_workflow'", INDEX)
        self.assertIn("localStorage.removeItem('hof_agent_landing_source')", INDEX)
        self.assertIn("{ source: agentLandingSource, workflow: agentLandingWorkflow || 'transaction_picker' }", INDEX)

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
        self.assertNotIn("agent_landing_question_one_opened", AGENTS)
        self.assertNotIn("agentQuestionOneCta", AGENTS)
        self.assertIn("agent_landing_cta_selected", AGENTS)
        self.assertIn("utm_source=agent_workspace", INDEX)
        self.assertIn("window.location.pathname === '/agents'", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertIn("utm_medium=agent_page", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertNotIn("hofAgentFormLibraryCta", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertNotIn("See the shared form library", (ROOT / "assets" / "pwa-register.js").read_text(encoding="utf-8"))
        self.assertIn("const params=new URLSearchParams(window.location.search)", AGENTS)
        self.assertIn("'direct_outreach','email','social','referral','local_event','print'", AGENTS)
        self.assertIn("source==='homeofferflow_admin'&&outreach.has(medium)?medium", AGENTS)
        self.assertIn("window.hofAgentLandingChannel=channel", AGENTS)
        self.assertIn("[data-agent-cta-path]", AGENTS)
        focus = (ROOT / "assets" / "agent-landing-focus.js").read_text(encoding="utf-8")
        self.assertIn("window.hofAgentLandingChannel ||", focus)

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

    def test_agent_transaction_selector_campaign_is_validated_but_not_attached_to_selector_clicks(self):
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
        self.assertIn("rate !== null", INDEX)
        self.assertIn("agent_landing_cta_counts_by_campaign[campaign] <= agent_landing_view_counts_by_campaign[campaign]", ADMIN)

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
            'agentFormPackageStartedCount', 'agentFormPackageStartRate',
            'agentFormPackageHandoffRecoveryCount',
            'agentFormPackageNestedChoiceCount', 'agentFormPackageNestedChoiceRate',
            'agentFormPackageInterviewCountsByWorkflow', 'agentFormPackageSelectionCountsByWorkflow', 'agentFormPackageStartedCountsByWorkflow', 'agentFormPackageNestedChoiceCountsByWorkflow',
            'agent_workflow_lease_representation_selected',
        ):
            self.assertIn(expected, ADMIN)
        self.assertIn("Agent Workspace Funnel", INDEX)
        self.assertIn("agentLandingCtaRate", INDEX)
        self.assertIn("agentLandingQuestionOneViewRate", INDEX)
        self.assertIn("agentLandingQuestionOneOpenRate", INDEX)
        self.assertIn("Channel views / workspace starts", INDEX)
        self.assertIn("continued to the workspace", INDEX)
        self.assertIn("Agent channel conversion:", INDEX)
        self.assertIn("agentLandingViewCountsByChannel?.referral", INDEX)
        self.assertIn("agentLandingDraftHandoffUserCount", INDEX)
        self.assertIn("agentLandingDraftHandoffRate", INDEX)
        self.assertIn("% of landing views", INDEX)
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
        self.assertIn("agentFormPackageStartRate", INDEX)
        self.assertIn("agentFormPackageNestedChoiceRate", INDEX)
        self.assertIn("agentFormPackageSelectionCountsByWorkflow?.lease_representation", INDEX)
        self.assertIn("agentFormPackageStartedCountsByWorkflow?.lease_representation", INDEX)
        self.assertIn("agentFormPackageNestedChoiceCountsByWorkflow?.lease_representation", INDEX)
        self.assertIn("agentWorkflowGuideCtaPathCounts?.relationship_drafts", INDEX)
        self.assertIn("agentWorkflowGuideCtaRate", INDEX)

    def test_question_two_conversion_excludes_pre_instrumentation_selections(self):
        self.assertIn("agent_form_package_interview_started_at", ADMIN)
        self.assertIn("agent_form_package_selection_events", ADMIN)
        self.assertIn("agent_form_package_started_events", ADMIN)
        self.assertIn("created_at >= first_view_at", ADMIN)

    def test_homepage_offer_entry_events_keep_anonymous_campaign_source(self):
        self.assertIn("const entrySource = String(new URLSearchParams(window.location.search).get('utm_source') || 'homepage')", INDEX)
        self.assertIn("source: entrySource", INDEX)


if __name__ == "__main__":
    unittest.main()
