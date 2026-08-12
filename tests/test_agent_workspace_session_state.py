from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AgentWorkspaceSessionStateTests(unittest.TestCase):
    def test_workspace_controls_persist_during_the_agent_session(self):
        self.assertIn("hof_offer_workspace_state_v1", HTML)
        self.assertIn("function savedWorkspaceState()", HTML)
        self.assertIn("function persistWorkspaceState()", HTML)
        self.assertIn("persistWorkspaceState(); rerender();", HTML)

    def test_workspace_reports_the_current_view_and_can_reset_it(self):
        self.assertIn("offer-workspace-result-summary", HTML)
        self.assertIn("of ${safe.length} loaded offer", HTML)
        self.assertIn("hofClearOfferWorkspaceFilters()", HTML)
        self.assertIn("Reset view", HTML)

    def test_workspace_filter_controls_expose_state_and_names(self):
        self.assertIn('aria-pressed="${state.filter===key ? \'true\' : \'false\'}"', HTML)
        self.assertIn('aria-label="Search saved offers"', HTML)
        self.assertIn('aria-label="Sort saved offers"', HTML)


if __name__ == "__main__":
    unittest.main()
