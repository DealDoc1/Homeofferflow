import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text())
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "api" / "admin-dashboard.py").read_text(encoding="utf-8")


class PwaOfferReviewShortcutTests(unittest.TestCase):
    def test_manifest_exposes_a_private_offer_review_shortcut(self):
        shortcuts = {item["url"]: item for item in MANIFEST["shortcuts"]}
        shortcut = shortcuts["/?pwa_action=offer_review"]
        self.assertEqual(shortcut["name"], "Offer Review")
        self.assertIn("risk review workspace", shortcut["description"])

    def test_shortcut_routes_an_agent_to_offer_review_and_keeps_investors_in_their_own_workspace(self):
        self.assertIn("async function openOfferReviewShortcut(role)", HTML)
        self.assertIn("if (role === 'investor')", HTML)
        self.assertIn("window.openAccountDashboard?.({ tab: 'offers' });", HTML)
        self.assertIn("window.openAccountDashboard?.({ tab: 'ai' });", HTML)
        self.assertIn("else if (action === 'offer_review') await openOfferReviewShortcut(role);", HTML)
        self.assertIn("else if (action === 'offer_review') await openOfferReviewShortcut(window.hofAuth?.role === 'investor' ? 'investor' : 'agent');", HTML)

    def test_aggregate_admin_analytics_include_offer_review_and_attention_shortcuts(self):
        self.assertIn('"offer_review"', ADMIN)
        self.assertIn('"attention_queue"', ADMIN)
        self.assertIn("pwaAuthenticatedShortcutCounts?.offer_review", HTML)
        self.assertIn("pwaAuthenticatedShortcutCounts?.attention_queue", HTML)


if __name__ == "__main__":
    unittest.main()
