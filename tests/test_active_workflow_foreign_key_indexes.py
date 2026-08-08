import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase/migrations/20260808150000_active_workflow_foreign_key_indexes.sql"
).read_text(encoding="utf-8")


class ActiveWorkflowForeignKeyIndexTests(unittest.TestCase):
    def test_migration_covers_live_advisor_missing_foreign_keys(self):
        expected = (
            "hof_ai_offer_reviews_user_id_idx",
            "hof_brokerage_members_txr_agent_attested_by_idx",
            "hof_listing_workspaces_seller_lead_id_idx",
            "hof_seller_disclosure_drafts_disclosure_source_id_idx",
            "hof_seller_disclosure_drafts_listing_workspace_id_idx",
            "hof_seller_disclosure_drafts_seller_review_attested_by_idx",
            "hof_seller_disclosure_drafts_water_source_id_idx",
            "hof_seller_disclosure_review_links_agent_user_id_idx",
            "hof_seller_disclosure_review_links_brokerage_id_idx",
            "hof_seller_leads_brokerage_id_idx",
            "hof_seller_leads_user_id_idx",
            "hof_standalone_agreements_form_source_id_idx",
            "hof_usage_events_offer_id_idx",
        )
        for index_name in expected:
            self.assertIn(f"create index if not exists {index_name}", MIGRATION)


if __name__ == "__main__":
    unittest.main()
