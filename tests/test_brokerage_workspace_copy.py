import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class BrokerageWorkspaceCopyTests(unittest.TestCase):
    def test_brokerage_copy_describes_the_available_privacy_limited_workspace(self):
        source = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn("Brokerage / Team Lead Workspace", source)
        self.assertIn("secure invite links", source)
        self.assertIn("Buyer names, addresses, offer terms, and documents are not exposed here.", source)
        self.assertNotIn("The next layer can add agent invites", source)


if __name__ == "__main__":
    unittest.main()
