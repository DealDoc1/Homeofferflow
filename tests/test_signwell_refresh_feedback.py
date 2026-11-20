from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class SignWellRefreshFeedbackTests(unittest.TestCase):
    def test_workspace_status_is_exported_for_signature_refresh_feedback(self):
        self.assertIn("root.announceWorkspaceStatus = announceWorkspaceStatus;", INDEX)
        start = INDEX.index("async function refreshSignWellStatus(")
        end = INDEX.index("const offerSigningStatusRequests", start)
        handler = INDEX[start:end]
        self.assertIn("window.announceWorkspaceStatus?.(", handler)
        self.assertIn("Couldn’t check signing status. Try again.", handler)
        self.assertNotIn("alert(", handler)

    def test_missing_auth_uses_auth_status(self):
        self.assertIn("setAuthStatus('Please sign in before refreshing SignWell status.', 'err')", INDEX)
        self.assertNotIn("alert('Please sign in before refreshing SignWell status.')", INDEX)


if __name__ == "__main__":
    unittest.main()
