import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TrialRenewalNoticeUrgencyTests(unittest.TestCase):
    def test_trial_notice_surfaces_three_day_urgency_and_billing_cta(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("trialDaysRemaining", source)
        self.assertIn("ends in ' + trialDaysRemaining", source)
        self.assertIn("Review Manage Billing", source)
        self.assertIn("openBillingPortal()", source)


if __name__ == "__main__":
    unittest.main()
