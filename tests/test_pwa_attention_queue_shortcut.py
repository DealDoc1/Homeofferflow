import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text())
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class PwaAttentionQueueShortcutTests(unittest.TestCase):
    def test_manifest_exposes_a_private_attention_recovery_shortcut(self):
        shortcuts = {item["url"]: item for item in MANIFEST["shortcuts"]}
        shortcut = shortcuts["/?pwa_action=attention_queue"]
        self.assertEqual(shortcut["name"], "Needs Attention")
        self.assertIn("expired signing recovery", shortcut["description"])

    def test_shortcut_routes_signed_in_agents_to_the_private_attention_filter(self):
        self.assertIn("'attention_queue'", HTML)
        self.assertIn("async function openAttentionQueue()", HTML)
        self.assertIn("window.hofSetOfferWorkspaceFilter?.('attention');", HTML)
        self.assertIn("else if (action === 'attention_queue') await openAttentionQueue();", HTML)


if __name__ == "__main__":
    unittest.main()
