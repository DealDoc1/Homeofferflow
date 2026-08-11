import pathlib
import unittest


HTML = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class SubscriptionNearLimitNoticeTests(unittest.TestCase):
    def test_usage_card_warns_before_access_is_exhausted(self):
        self.assertIn("const nearLimit = usageAvailable && hasActiveAccess && good && pct >= 80", HTML)
        self.assertIn("Almost at this month’s packet limit", HTML)
        self.assertIn("review billing options before access pauses", HTML)
        self.assertIn("subscription_usage_near_limit_viewed", HTML)
        self.assertIn("usage_near_limit", HTML)
        self.assertIn("Review Manage Billing", HTML)
        self.assertIn("usage_exhausted", HTML)
        self.assertIn("Monthly packet allowance used", HTML)


if __name__ == "__main__":
    unittest.main()
