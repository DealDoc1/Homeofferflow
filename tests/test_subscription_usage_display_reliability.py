from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class SubscriptionUsageDisplayReliabilityTests(unittest.TestCase):
    def test_failed_usage_read_is_not_presented_as_zero_usage(self):
        self.assertIn("hofAuth.usage = { used: 0, limit, billingMonth, available: false };", HTML)
        self.assertIn("Usage is temporarily unavailable", HTML)
        self.assertIn("Refresh usage", HTML)

    def test_known_usage_retains_explicit_authoritative_state(self):
        self.assertIn("billingMonth: data.billingMonth || billingMonth, available: true", HTML)
        self.assertIn("const usageAvailable = usage.available !== false;", HTML)

    def test_generation_screen_does_not_treat_an_unknown_read_as_exhausted(self):
        self.assertIn("if (usage.available !== false && Number(usage.used || 0) >= Number(usage.limit || 10))", HTML)
        self.assertIn("The server will verify your current allowance before packet generation.", HTML)


if __name__ == "__main__":
    unittest.main()
