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
        self.assertIn("root.hofRefreshOfferWorkspace = async function({ automatic = false } = {})", HTML)
        self.assertIn("new Set(['created', 'sent', 'viewed', 'partially_signed', 'awaiting_signature', 'in_progress'])", HTML)
        self.assertIn("Promise.allSettled(active.map(offer => root.refreshSignWellStatus", HTML)
        self.assertIn("return aUpdated - bUpdated;", HTML)
        self.assertIn("slice(0, 10)", HTML)
        self.assertIn("skipReload = false, suppressAlert = false", HTML)
        self.assertIn("Sync signing status", HTML)

    def test_opening_offers_automatically_syncs_with_a_short_cooldown(self):
        self.assertIn("window.hofRefreshOfferWorkspace({ automatic: true })", HTML)
        self.assertIn("let lastAutomaticSigningSyncAt = 0;", HTML)
        self.assertIn("now - lastAutomaticSigningSyncAt < 120000", HTML)
        self.assertIn("window.refreshSignWellStatus = refreshSignWellStatus;", HTML)

    def test_workspace_has_a_stale_draft_and_signing_attention_queue(self):
        self.assertIn("function needsAttention(o)", HTML)
        self.assertIn("Needs attention", HTML)
        self.assertIn("Resume this stale draft", HTML)
        self.assertIn("Refresh signing status and follow up", HTML)


if __name__ == "__main__":
    unittest.main()
