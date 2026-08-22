import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class AccountWorkspaceLoadingResilienceTests(unittest.TestCase):
    def test_account_shell_opens_before_remote_workspace_loads(self):
        start = HTML.index("async function openAccountDashboard(opts = {})")
        end = HTML.index("function closeAccountDashboard()", start)
        workspace = HTML[start:end]

        self.assertLess(workspace.index("modal.classList.add('active')"), workspace.index("await loadAccountProfile()"))
        self.assertIn("Opening your workspace…", workspace)
        self.assertIn("dashboard.setAttribute('aria-busy', 'true')", workspace)

    def test_remote_workspace_failures_are_visible_and_retryable(self):
        start = HTML.index("async function openAccountDashboard(opts = {})")
        end = HTML.index("function closeAccountDashboard()", start)
        workspace = HTML[start:end]

        self.assertIn("Account workspace load failed:", workspace)
        self.assertIn("Workspace needs a refresh", workspace)
        self.assertIn("Try again", workspace)
        self.assertIn("Open Brokerage Setup", workspace)
        self.assertIn("no account data was changed", workspace)


if __name__ == "__main__":
    unittest.main()
