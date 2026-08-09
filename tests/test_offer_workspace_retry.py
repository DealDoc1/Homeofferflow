from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferWorkspaceRetryTests(unittest.TestCase):
    def test_offer_loader_keeps_a_recovery_action_on_transient_failure(self):
        start = HTML.index("async function loadMyOffers()")
        end = HTML.index("function formatOfferDate", start)
        loader = HTML[start:end]
        self.assertIn("Could not load offers yet.", loader)
        self.assertIn('onclick="loadMyOffers()"', loader)
        self.assertIn("Retry offers", loader)

    def test_workspace_refresh_syncs_active_signwell_documents_before_reload(self):
        self.assertIn("root.hofRefreshOfferWorkspace = async function()", HTML)
        self.assertIn("Promise.allSettled(active.map(offer => root.refreshSignWellStatus", HTML)
        self.assertIn("slice(0, 5)", HTML)
        self.assertIn("skipReload = false, suppressAlert = false", HTML)
        self.assertIn("Sync signing status", HTML)


if __name__ == "__main__":
    unittest.main()
