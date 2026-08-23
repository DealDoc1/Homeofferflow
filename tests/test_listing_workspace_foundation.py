from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_listing_workspaces.sql").read_text()
SERVER_ONLY_MIGRATION = (ROOT / "supabase" / "homeofferflow_listing_workspace_summary_server_only.sql").read_text()
HARDENING_MIGRATION = (ROOT / "supabase" / "homeofferflow_listing_workspace_hardening.sql").read_text()
OFFER_COMPARISON_MIGRATION = (ROOT / "supabase" / "migrations" / "20260808201500_listing_workspace_offer_comparison.sql").read_text()
DOC = (ROOT / "docs" / "SELLER_LISTING_WORKSPACE_FOUNDATION.md").read_text()
INDEX = (ROOT / "index.html").read_text()


class ListingWorkspaceFoundationTests(unittest.TestCase):
    def test_optional_seller_lead_email_is_validated_before_the_private_record_is_saved(self):
        self.assertIn('id="sellerLeadEmail" type="email" inputmode="email" autocomplete="email"', INDEX)
        start = INDEX.index("async function saveSellerLeadFoundation()")
        end = INDEX.index("async function loadSellerLeadsFoundation()", start)
        save = INDEX[start:end]
        self.assertIn("sellerEmailInput?.checkValidity()", save)
        self.assertIn("sellerEmailInput.focus();", save)

    def test_seller_lead_save_prevents_duplicate_submissions_and_announces_progress(self):
        self.assertIn('id="saveSellerLeadButton"', INDEX)
        self.assertIn('id="sellerFoundationStatus" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', INDEX)
        start = INDEX.index("async function saveSellerLeadFoundation()")
        end = INDEX.index("async function loadSellerLeadsFoundation()", start)
        save = INDEX[start:end]
        self.assertIn("const saveButton = document.getElementById('saveSellerLeadButton');", save)
        self.assertIn("if (saveButton?.disabled) return;", save)
        self.assertIn("saveButton.disabled = true", save)
        self.assertIn("saveButton.setAttribute('aria-busy', 'true')", save)
        self.assertIn("saveButton.textContent = 'Saving seller lead…'", save)
        self.assertIn("Saving seller lead details…", save)
        self.assertIn("saveButton.disabled = false", save)
        self.assertIn("saveButton.textContent = 'Save Seller Lead'", save)

    def test_workspace_is_separate_from_buyer_offers_and_form_execution(self):
        self.assertIn("create table if not exists public.hof_listing_workspaces", MIGRATION)
        self.assertIn("does not create, send, or sign", MIGRATION)
        self.assertIn("does not create representation", DOC)

    def test_agent_owns_sensitive_listing_workspace_data(self):
        self.assertIn("hof_listing_workspaces_agent_select_own", MIGRATION)
        self.assertIn("agent_user_id = (select auth.uid())", MIGRATION)
        self.assertIn("confidential_notes text", MIGRATION)
        self.assertIn("seller_names text[]", MIGRATION)

    def test_broker_summary_is_aggregate_only(self):
        self.assertIn("hof_brokerage_listing_workspace_summary", MIGRATION)
        self.assertIn("count(*)::bigint", MIGRATION)
        self.assertIn("never seller names, addresses, notes", MIGRATION)
        self.assertIn("aggregate sale/lease/status counts", DOC)

    def test_broker_summary_is_not_anonymous_rpc(self):
        self.assertIn(
            "revoke all on function public.hof_brokerage_listing_workspace_summary() from anon;",
            MIGRATION,
        )

    def test_dashboard_workspace_ui_preserves_private_form_boundary(self):
        self.assertIn("workspaceTitle", INDEX)
        self.assertIn("saveListingWorkspaceFoundation", INDEX)
        self.assertIn("hof_listing_workspaces", INDEX)
        self.assertIn("/api/admin-dashboard?scope=brokerage", INDEX)
        self.assertNotIn("client.rpc('hof_brokerage_listing_workspace_summary')", INDEX)
        self.assertIn("It has not created a form or signature request.", INDEX)

    def test_broker_summary_uses_server_authorized_aggregate_only_payload(self):
        admin = (ROOT / "api" / "admin-dashboard.py").read_text()
        start = admin.index("async def _brokerage_dashboard_payload")
        end = admin.index("def _normalized_invite_email", start)
        segment = admin[start:end]
        self.assertIn("listingWorkspaceSummary", segment)
        self.assertIn("&select=listing_kind,status", segment)
        for sensitive in ("seller_names", "property_address", "confidential_notes", "requested_workflows"):
            self.assertNotIn(sensitive, segment)

    def test_server_only_migration_revokes_browser_execution(self):
        self.assertIn(
            "revoke all on function public.hof_brokerage_listing_workspace_summary() from authenticated;",
            SERVER_ONLY_MIGRATION,
        )
        self.assertIn(
            "grant execute on function public.hof_brokerage_listing_workspace_summary() to service_role;",
            SERVER_ONLY_MIGRATION,
        )

    def test_dashboard_shows_source_readiness_without_activating_forms(self):
        self.assertIn("Listing Form Readiness", INDEX)
        self.assertIn("loadListingWorkspaceSourceReadiness", INDEX)
        self.assertIn("Execution remains unavailable until its source-specific workflow is ready.", INDEX)
        self.assertIn("TXR-1101", INDEX)
        self.assertIn("TXR-1406", INDEX)

    def test_transaction_first_listing_selection_moves_to_the_property_address_question(self):
        tab_start = INDEX.index("function showAccountTab(tab = 'dashboard')")
        tab_end = INDEX.index("function renderRelationshipDraftsPanel()", tab_start)
        tabs = INDEX[tab_start:tab_end]
        self.assertIn("['sale_listing', 'lease_listing'].includes(window.hofAgentWorkflowContext)", tabs)
        self.assertIn("document.getElementById('listingWorkspaceAddress')", tabs)
        self.assertIn("address?.scrollIntoView({ behavior: 'smooth', block: 'center' });", tabs)
        self.assertIn("address?.focus({ preventScroll: true });", tabs)

    def test_transaction_first_listing_workspace_starts_with_a_property_question(self):
        self.assertIn("<div class=\"eyebrow\" style=\"margin-bottom:.35rem;\">Question 2</div>", INDEX)
        self.assertIn("Which property is this listing for?", INDEX)
        self.assertIn("Which property is this lease listing for?", INDEX)
        self.assertIn("Seller name(s)", INDEX)
        self.assertIn("Landlord name(s)", INDEX)

    def test_optional_planning_topics_do_not_compete_with_the_listing_intake(self):
        self.assertIn("Add optional planning topics", INDEX)
        self.assertIn("Leave this closed if you only need a private listing workspace now.", INDEX)
        self.assertIn("they do not select, create, send, or sign a form.", INDEX)
        self.assertIn("<details class=\"field\" style=\"margin-top:0.8rem;\">", INDEX)

    def test_new_workspace_becomes_the_active_next_step_workspace(self):
        start = INDEX.index("async function saveListingWorkspaceFoundation()")
        end = INDEX.index("function listingWorkspaceLabel", start)
        save = INDEX[start:end]
        self.assertIn("insert(payload).select('id').single()", save)
        self.assertIn("listingLaunchWorkspace", save)
        self.assertIn("listingOfferWorkspace", save)
        self.assertIn("listingLaunchChecklistCard", save)
        self.assertIn("loadListingWorkspaceOffersFoundation()", save)
        self.assertIn("default to an older property", save)

    def test_workspace_creation_prevents_duplicate_submissions_and_announces_progress(self):
        start = INDEX.index("async function saveListingWorkspaceFoundation()")
        end = INDEX.index("function listingWorkspaceLabel", start)
        save = INDEX[start:end]
        self.assertIn('id="createListingWorkspaceButton"', INDEX)
        self.assertIn('id="listingWorkspaceStatus" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', INDEX)
        self.assertIn("const createButton = document.getElementById('createListingWorkspaceButton');", save)
        self.assertIn("if (createButton?.disabled) return;", save)
        self.assertIn("createButton.disabled = true", save)
        self.assertIn("createButton.setAttribute('aria-busy', 'true')", save)
        self.assertIn("createButton.textContent = 'Creating workspace…'", save)
        self.assertIn("Creating your private listing workspace…", save)
        self.assertIn("createButton.disabled = false", save)
        self.assertIn("createButton.textContent = 'Create Private Workspace'", save)

    def test_missing_brokerage_uses_self_service_setup_without_losing_listing_question_answers(self):
        render_start = INDEX.index("function renderSellerFoundationPanel()")
        render_end = INDEX.index("const sellerCampaignPackages", render_start)
        render = INDEX[render_start:render_end]
        self.assertIn("window.__hofListingWorkspaceSetupDraft", render)
        self.assertIn("Your listing details are ready.", render)
        save_start = INDEX.index("async function saveListingWorkspaceFoundation()")
        save_end = INDEX.index("function listingWorkspaceLabel", save_start)
        save = INDEX[save_start:save_end]
        self.assertIn("showAccountTab('brokerage');", save)
        self.assertIn("Save your brokerage foundation to finish this private listing workspace.", save)
        self.assertIn("Your entered property and seller details stay in this browser session.", save)
        self.assertIn("delete window.__hofListingWorkspaceSetupDraft;", save)
        self.assertNotIn("Contact support before creating a listing workspace.", save)

    def test_workspace_hardening_allowlists_requested_workflows_and_refreshes_timestamp(self):
        self.assertIn("hof_listing_workspaces_requested_workflows_allowed", HARDENING_MIGRATION)
        self.assertIn("hof_listing_workflows_allowed(value jsonb)", HARDENING_MIGRATION)
        for workflow in ("listing_agreement", "seller_disclosure", "lease_listing"):
            self.assertIn(f"'{workflow}'", HARDENING_MIGRATION)
        self.assertIn("hof_listing_workspaces_touch_updated_at", HARDENING_MIGRATION)
        self.assertIn("new.updated_at = now()", HARDENING_MIGRATION)

    def test_seller_status_notice_explains_live_boundary(self):
        self.assertIn("Start here:", INDEX)
        self.assertIn("executable listing agreements, seller disclosures, and lease-listing packets", INDEX.lower())
        self.assertIn("completed-signature visual QA", INDEX)
        self.assertIn("Agent-side seller planning tools:", INDEX)
        self.assertNotIn("Agent-side seller-representation tools: listing packet", INDEX)

    def test_saved_seller_lead_can_seed_a_private_workspace(self):
        self.assertIn("startListingWorkspaceFromLead", INDEX)
        self.assertIn("Prepare listing workspace", INDEX)
        self.assertIn("Seller lead details copied into a linked private listing workspace draft", INDEX)
        self.assertIn("seller-lead-actions", INDEX)

    def test_seeded_workspace_preserves_only_the_agents_own_seller_lead_link(self):
        self.assertIn("dataset.sellerLeadId = id", INDEX)
        self.assertIn("seller_lead_id:", INDEX)
        self.assertIn("hofPlatform.sellerLeads.some", INDEX)
        self.assertIn("delete document.getElementById('listingWorkspaceAddress').dataset.sellerLeadId", INDEX)

    def test_private_offer_comparison_worksheet_is_owner_scoped(self):
        self.assertIn("create table if not exists public.hof_listing_workspace_offers", OFFER_COMPARISON_MIGRATION)
        self.assertIn("alter table public.hof_listing_workspace_offers enable row level security", OFFER_COMPARISON_MIGRATION)
        self.assertIn("hof_listing_workspace_offers_select_own", OFFER_COMPARISON_MIGRATION)
        self.assertIn("hof_listing_workspace_offers_insert_own", OFFER_COMPARISON_MIGRATION)
        self.assertIn("hof_listing_workspace_offers_update_own", OFFER_COMPARISON_MIGRATION)
        self.assertIn("hof_listing_workspace_offers_delete_own", OFFER_COMPARISON_MIGRATION)
        self.assertIn("Seller Offer Comparison Worksheet", INDEX)
        self.assertIn("saveListingWorkspaceOffer", INDEX)
        self.assertIn("updateListingWorkspaceOfferStatus", INDEX)
        self.assertIn("Save status", INDEX)
        self.assertIn("deleteListingWorkspaceOffer", INDEX)
        self.assertIn("Remove", INDEX)
        self.assertIn(".eq('agent_user_id', user.id)", INDEX)
        self.assertIn("updateListingWorkspaceStatus", INDEX)
        self.assertIn("listingWorkspaceStatusOptions", INDEX)
        self.assertIn("It is not a recommendation or contract decision.", INDEX)

    def test_private_offer_comparison_can_copy_a_non_recommendatory_review_summary(self):
        self.assertIn("copyListingWorkspaceOfferSummary", INDEX)
        self.assertIn("Copy Seller Review Summary", INDEX)
        self.assertIn("private seller offer-comparison worksheet", INDEX)
        self.assertIn("It does not rank, recommend, accept, reject, or create a contract.", INDEX)

    def test_offer_comparison_save_prevents_duplicate_submissions_and_announces_progress(self):
        self.assertIn('id="saveListingWorkspaceOfferButton"', INDEX)
        self.assertIn('id="listingOfferStatusMessage" class="platform-status" role="status" aria-live="polite" aria-atomic="true"', INDEX)
        start = INDEX.index("async function saveListingWorkspaceOffer()")
        end = INDEX.index("async function loadListingWorkspacesFoundation()", start)
        save = INDEX[start:end]
        self.assertIn("const saveButton = document.getElementById('saveListingWorkspaceOfferButton');", save)
        self.assertIn("if (saveButton?.disabled) return;", save)
        self.assertIn("saveButton.disabled = true", save)
        self.assertIn("saveButton.setAttribute('aria-busy', 'true')", save)
        self.assertIn("saveButton.textContent = 'Saving comparison…'", save)
        self.assertIn("saveButton.disabled = false", save)
        self.assertIn("saveButton.textContent = 'Save Offer Comparison'", save)

    def test_private_offer_comparison_can_prepare_an_estimated_proceeds_worksheet_without_ranking_offers(self):
        self.assertIn("Estimated seller proceeds comparison", INDEX)
        self.assertIn("calculateListingOfferNetComparison", INDEX)
        self.assertIn("copyListingOfferNetComparison", INDEX)
        self.assertIn("printListingOfferNetComparison", INDEX)
        self.assertIn("listingOfferNetRows", INDEX)
        self.assertIn("Estimated proceeds before unentered items", INDEX)
        self.assertIn("It does not calculate a closing statement, determine commissions, account for every obligation, rank offers, or recommend a decision.", INDEX)
        self.assertIn("This is not a closing statement, valuation, legal or tax advice, offer ranking, recommendation, acceptance, rejection, or contract decision.", INDEX)

    def test_listing_workspace_can_generate_a_non_executable_listing_kickoff_checklist(self):
        self.assertIn("Listing Kickoff Checklist", INDEX)
        self.assertIn("copyListingLaunchChecklist", INDEX)
        self.assertIn("printListingLaunchChecklist", INDEX)
        self.assertIn("listingLaunchChecklistText", INDEX)
        self.assertIn("listingWorkspaceContext", INDEX)
        self.assertIn("Lease Listing Kickoff Checklist", INDEX)
        self.assertIn("Application and lease handling", INDEX)
        self.assertIn("It is a planning aid only", INDEX)
        self.assertIn("not legal advice, a pricing opinion, a listing agreement, disclosure, contract, or instruction to sign", INDEX)
        self.assertIn("hofPlatform.listingWorkspaces = workspaces", INDEX)

    def test_listing_workspace_can_generate_a_private_non_executable_listing_consultation_brief(self):
        self.assertIn("Listing Consultation Brief", INDEX)
        self.assertIn("copySellerConsultationBrief", INDEX)
        self.assertIn("printSellerConsultationBrief", INDEX)
        self.assertIn("sellerConsultationBriefText", INDEX)
        self.assertIn("Lease Listing Consultation Brief", INDEX)
        self.assertIn("Lease preparation", INDEX)
        self.assertIn("Choose a private listing workspace above first.", INDEX)
        self.assertIn("It is a private planning document—not a listing agreement, disclosure, pricing opinion, contract, or instruction to sign.", INDEX)
        self.assertIn("Do not create, send, sign, or describe a listing agreement, disclosure, or lease packet as executable", INDEX)


if __name__ == "__main__":
    unittest.main()
