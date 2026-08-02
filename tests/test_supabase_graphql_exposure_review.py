import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs" / "SUPABASE_GRAPHQL_EXPOSURE_REVIEW.md").read_text(encoding="utf-8")


class SupabaseGraphqlExposureReviewTests(unittest.TestCase):
    def test_review_records_the_non_destructive_decision(self):
        self.assertIn("Do not revoke `authenticated` access or drop `pg_graphql`", DOC)
        self.assertIn("RLS\nand table grants remain the actual authorization boundary", DOC)

    def test_review_covers_sensitive_browser_dependencies(self):
        for table_name in (
            "hof_offers",
            "hof_profiles",
            "hof_subscriptions",
            "hof_brokerages",
            "hof_brokerage_members",
            "hof_agent_documents",
            "hof_standalone_agreements",
        ):
            self.assertIn(f"`{table_name}`", DOC)

    def test_review_preserves_the_migration_sequence(self):
        self.assertIn("Move one sensitive browser dependency at a time", DOC)
        self.assertIn("the API path and direct-browser denial", DOC)
        self.assertIn("Do not apply a blanket `revoke all ... from authenticated` migration", DOC)

    def test_feedback_has_a_server_only_grant_migration(self):
        migration = (ROOT / "supabase" / "homeofferflow_feedback_server_only.sql").read_text(encoding="utf-8")
        self.assertIn("revoke all on table public.hof_feedback from anon, authenticated", migration)
        self.assertIn("grant all on table public.hof_feedback to service_role", migration)


if __name__ == "__main__":
    unittest.main()
