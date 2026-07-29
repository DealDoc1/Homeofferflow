from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRACKER_SEED = (ROOT / "supabase" / "homeofferflow_product_tracker.sql").read_text(encoding="utf-8")
REVENUE_PRIORITY = (ROOT / "supabase" / "homeofferflow_revenue_priority_2026_07.sql").read_text(encoding="utf-8")


class ProductTrackerSeedTests(unittest.TestCase):
    def test_seo_hero_seed_matches_the_verified_production_launch(self):
        self.assertIn("'seo-hero-update', 'Marketing', 'SEO hero update'", TRACKER_SEED)
        self.assertIn("34, 'production', 'production', 'passed'", TRACKER_SEED)
        self.assertIn("'Launch messaging production release 57f768d'", TRACKER_SEED)
        self.assertNotIn("Approved headline is not deployed.", TRACKER_SEED)

    def test_revenue_priority_does_not_recommend_redeploying_the_live_hero(self):
        self.assertIn("'seo-hero-update', 4, 'grow_now'", REVENUE_PRIORITY)
        self.assertIn("'Monitor launch conversion and keep the Texas offer scope wording current", REVENUE_PRIORITY)
        self.assertNotIn("Deploy the approved hero", REVENUE_PRIORITY)


if __name__ == "__main__":
    unittest.main()
