import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER_SEED = ROOT / "supabase" / "homeofferflow_product_tracker.sql"


class ProductTrackerSeedSafetyTests(unittest.TestCase):
    def test_seed_never_overwrites_live_release_or_qa_status(self):
        sql = TRACKER_SEED.read_text(encoding="utf-8").lower()

        self.assertIn("on conflict (slug) do nothing", sql)
        self.assertNotIn("on conflict (slug) do update set", sql)


if __name__ == "__main__":
    unittest.main()
