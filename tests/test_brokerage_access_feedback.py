from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BrokerageAccessFeedbackTests(unittest.TestCase):
    def test_brokerage_access_errors_use_workspace_status(self):
        segment = INDEX[INDEX.index("root.setBrokerageMemberStatus"):INDEX.index("root.saveBrokerageBranding")]
        self.assertIn("window.announceWorkspaceStatus?.('Sign in again before changing brokerage access.')", segment)
        self.assertIn("window.hofCustomerActionError?.(error, 'We couldn’t update brokerage access. Please try again.')", segment)
        self.assertIn("window.announceWorkspaceStatus?.('Sign in again before inviting an agent.')", segment)
        self.assertIn("window.hofCustomerActionError?.(error, 'We couldn’t cancel that invitation. Please try again.')", segment)
        self.assertNotIn('alert(', segment)


if __name__ == "__main__":
    unittest.main()
