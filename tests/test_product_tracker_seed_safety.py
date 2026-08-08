import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER_SEED = ROOT / "supabase" / "homeofferflow_product_tracker.sql"
PRODUCT_TRACKER_MIGRATION = ROOT / "supabase" / "migrations" / "20260721175340_homeofferflow_product_tracker.sql"


class ProductTrackerSeedSafetyTests(unittest.TestCase):
    def test_seed_never_overwrites_live_release_or_qa_status(self):
        sql = TRACKER_SEED.read_text(encoding="utf-8").lower()

        self.assertIn("on conflict (slug) do nothing", sql)
        self.assertNotIn("on conflict (slug) do update set", sql)

    def test_migration_recreates_qa_run_uniqueness_for_schema_baseline_replay(self):
        sql = PRODUCT_TRACKER_MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("create unique index if not exists hof_qa_runs_scenario_release_environment_key", sql)
        self.assertIn("on public.hof_qa_runs(scenario_id, release_name, environment)", sql)


if __name__ == "__main__":
    unittest.main()
