from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_listing_workspaces.sql").read_text()
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
        self.assertIn("hof_brokerage_listing_workspace_summary", INDEX)
        self.assertIn("It has not created a form or signature request.", INDEX)

    def test_dashboard_shows_source_readiness_without_activating_forms(self):
        self.assertIn("Listing Form Readiness", INDEX)
        self.assertIn("loadListingWorkspaceSourceReadiness", INDEX)
        self.assertIn("Execution remains gated.", INDEX)
        self.assertIn("TXR-1101", INDEX)
        self.assertIn("TXR-1406", INDEX)


if __name__ == "__main__":
    unittest.main()
