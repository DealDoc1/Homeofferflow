from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AgentWorkspaceTransactionEntryTests(unittest.TestCase):
    def test_workspace_starts_with_the_transaction_choice(self):
        start = HTML.index('<script id="hof-agent-workspace-v10-js">')
        end = HTML.index('</script>', start)
        workspace = HTML[start:end]

        self.assertIn('Transaction workspace', workspace)
        self.assertIn('Choose a transaction type to begin.', workspace)
        self.assertIn('onclick="startAccountTransaction()">Choose Transaction', workspace)
        self.assertNotIn('New Buyer Offer', workspace)

    def test_saved_purchase_offers_are_labeled_accurately(self):
        start = HTML.index('<script id="hof-agent-workspace-v10-js">')
        end = HTML.index('</script>', start)
        workspace = HTML[start:end]

        self.assertIn('Purchase offers', workspace)
        self.assertIn('Search saved purchase offers', workspace)
        self.assertIn('No saved purchase offers match this view.', workspace)


if __name__ == "__main__":
    unittest.main()
