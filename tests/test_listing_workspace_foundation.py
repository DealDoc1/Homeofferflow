from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_listing_workspaces.sql").read_text()
SERVER_ONLY_MIGRATION = (ROOT / "supabase" / "homeofferflow_listing_workspace_summary_server_only.sql").read_text()
HARDENING_MIGRATION = (ROOT / "supabase" / "homeofferflow_listing_workspace_hardening.sql").read_text()
DOC = (ROOT / "docs" / "SELLER_LISTING_WORKSPACE_FOUNDATION.md").read_text()
INDEX = (ROOT / "index.html").read_text()


class ListingWorkspaceFoundationTests(unittest.TestCase):
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
        self.assertIn("Private Listing Workspace", INDEX)
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
        self.assertIn("Execution remains gated.", INDEX)
        self.assertIn("TXR-1101", INDEX)
        self.assertIn("TXR-1406", INDEX)

    def test_workspace_hardening_allowlists_requested_workflows_and_refreshes_timestamp(self):
        self.assertIn("hof_listing_workspaces_requested_workflows_allowed", HARDENING_MIGRATION)
        for workflow in ("listing_agreement", "seller_disclosure", "lease_listing"):
            self.assertIn(f"'{workflow}'", HARDENING_MIGRATION)
        self.assertIn("hof_listing_workspaces_touch_updated_at", HARDENING_MIGRATION)
        self.assertIn("new.updated_at = now()", HARDENING_MIGRATION)

    def test_seller_status_notice_explains_live_boundary(self):
        self.assertIn("Seller-side launch status:", INDEX)
        self.assertIn("executable listing agreements, seller disclosures, and lease-listing packets", INDEX.lower())
        self.assertIn("completed-signature visual QA", INDEX)


if __name__ == "__main__":
    unittest.main()

