import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = (ROOT / "agents.html").read_text(encoding="utf-8")
SELLERS = (ROOT / "sellers.html").read_text(encoding="utf-8")


class LowNoisePublicPageTests(unittest.TestCase):
    def test_agent_hero_has_one_primary_action_and_one_exploration_path(self):
        hero = AGENTS.split('<section class="grid" id="transaction-start"', 1)[0]
        self.assertIn('>Choose a transaction<', hero)
        self.assertEqual(hero.count('class="button"'), 1)
        self.assertEqual(hero.count('class="button secondary"'), 0)

    def test_seller_hero_has_one_primary_action_and_one_comparison_path(self):
        hero = SELLERS.split('<section aria-labelledby="seller-next-steps">', 1)[0]
        self.assertIn('>Get my free seller plan<', hero)
        self.assertIn('>Compare support paths<', hero)
        self.assertEqual(hero.count('class="button"'), 1)
        self.assertEqual(hero.count('class="button secondary"'), 1)
        self.assertNotIn('Start where you are', hero)


if __name__ == "__main__":
    unittest.main()
