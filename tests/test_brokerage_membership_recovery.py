import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class BrokerageMembershipRecoveryTests(unittest.TestCase):
    def test_inactive_membership_has_a_user_initiated_recovery_path(self):
        self.assertIn("Brokerage access needs activation", HTML)
        self.assertIn("Request brokerage activation", HTML)
        self.assertIn("openBrokerageMembershipRequest", HTML)
        self.assertIn("issue.value = 'brokerage_access'", HTML)
        self.assertIn("does not change billing, roles, offers, or documents", HTML)

    def test_recovery_request_warns_not_to_include_transaction_details(self):
        self.assertIn("Do not include client, property, offer, or document details.", HTML)


if __name__ == "__main__":
    unittest.main()
