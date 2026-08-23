from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class SubscriptionGenerationFeedbackTests(unittest.TestCase):
    def test_subscription_gate_errors_use_existing_status_surfaces(self):
        self.assertIn("setSubscriptionActionStatus('We could not save your legal acceptance.", INDEX)
        self.assertIn("setSubscriptionActionStatus(data.error || message)", INDEX)
        self.assertIn("setAuthStatus('Please log in before generating an agent or investor packet.', 'err')", INDEX)
        self.assertNotIn("alert('We could not save your legal acceptance.", INDEX)
        self.assertNotIn("alert(data.error || message)", INDEX)


if __name__ == "__main__":
    unittest.main()
