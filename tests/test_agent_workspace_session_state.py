from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AgentWorkspaceSessionStateTests(unittest.TestCase):
    def test_workspace_controls_persist_during_the_agent_session(self):
        self.assertIn("hof_offer_workspace_state_v1", HTML)
        self.assertIn("function savedWorkspaceState()", HTML)
        self.assertIn("function persistWorkspaceState()", HTML)
        self.assertIn("persistWorkspaceState(); rerender();", HTML)


if __name__ == "__main__":
    unittest.main()
