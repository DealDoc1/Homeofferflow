import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (ROOT / "supabase" / "homeofferflow_usage_events_server_only.sql").read_text(encoding="utf-8")


class UsageEventsServerOnlyMigrationTests(unittest.TestCase):
    def test_usage_events_are_removed_from_browser_data_api(self):
        self.assertIn("alter table public.hof_usage_events enable row level security", MIGRATION)
        self.assertIn("revoke all on table public.hof_usage_events from anon, authenticated", MIGRATION)
        self.assertIn("grant all on table public.hof_usage_events to service_role", MIGRATION)
        self.assertIn("drop policy if exists", MIGRATION)


if __name__ == "__main__":
    unittest.main()
