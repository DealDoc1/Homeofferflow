import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepeatOfferMetricTests(unittest.TestCase):
    def test_admin_payload_exposes_repeat_offer_rate(self):
        source = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"agentRepeatOfferRate"', source)
        self.assertIn("len(agent_offer_counts)", source)

    def test_admin_dashboard_surfaces_repeat_offer_rate(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Repeat-Offer Agents", source)
        self.assertIn("agentRepeatOfferRate", source)


if __name__ == "__main__":
    unittest.main()
