import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentRetentionFollowUpTests(unittest.TestCase):
    def test_platform_queue_includes_privacy_safe_retention_outreach(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"retentionFollowUpCount"', backend)
        self.assertIn('"category": "retention"', backend)
        self.assertIn("Retention", frontend)
        self.assertIn("Keep your HomeOfferFlow workflow moving", frontend)


if __name__ == "__main__":
    unittest.main()
