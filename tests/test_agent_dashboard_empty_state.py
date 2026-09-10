from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AgentDashboardEmptyStateTests(unittest.TestCase):
    def test_empty_workspace_explains_the_next_step(self):
        start = HTML.index("function renderMyOffers(offers)")
        end = HTML.index("async function refreshSignWellStatus", start)
        renderer = HTML[start:end]

        self.assertIn('const offerList = rows ||', renderer)
        self.assertIn('Your workspace is ready.', renderer)
        self.assertIn('Choose a transaction type above to begin a guided document package.', renderer)
        self.assertIn('<div class="offer-crm-list">${offerList}</div>', renderer)

    def test_empty_state_has_its_own_clear_visual_treatment(self):
        self.assertIn('.offer-crm-empty {', HTML)
        self.assertIn('border:1px dashed rgba(255,255,255,.18);', HTML)


if __name__ == "__main__":
    unittest.main()
