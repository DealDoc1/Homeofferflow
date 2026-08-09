import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BillingPortalIntentMetricsTests(unittest.TestCase):
    def test_billing_portal_open_is_logged_and_counted(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"billingPortalOpenCount"', backend)
        self.assertIn('"billingPortalOpenBySource"', backend)
        self.assertIn("billing_portal_opened", frontend)
        self.assertIn("trial_renewal_urgency", frontend)
        self.assertIn("renewal_urgency", frontend)
        self.assertIn('Billing Portal Opens', frontend)


if __name__ == "__main__":
    unittest.main()
