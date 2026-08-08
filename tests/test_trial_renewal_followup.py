import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TrialRenewalFollowUpTests(unittest.TestCase):
    def test_platform_admin_surfaces_trial_renewal_queue(self):
        backend = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('"trialEndingSoonQueue"', backend)
        self.assertIn('"trialEndingSoonCount"', backend)
        self.assertIn('Trials Ending Soon', frontend)
        self.assertIn('Trial Renewal Follow-up', frontend)
        self.assertIn('Your HomeOfferFlow trial is nearing renewal', frontend)


if __name__ == "__main__":
    unittest.main()
