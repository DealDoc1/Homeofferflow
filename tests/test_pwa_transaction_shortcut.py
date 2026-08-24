from pathlib import Path
import json
import unittest


MANIFEST = json.loads((Path(__file__).resolve().parents[1] / "manifest.webmanifest").read_text(encoding="utf-8"))
SERVICE_WORKER = (Path(__file__).resolve().parents[1] / "service-worker.js").read_text(encoding="utf-8")


class PwaTransactionShortcutTests(unittest.TestCase):
    def test_installed_app_has_direct_transaction_start_shortcut(self):
        shortcut = next(item for item in MANIFEST["shortcuts"] if item["short_name"] == "Start")
        self.assertEqual(shortcut["url"], "/?pwa_action=transaction_start")
        self.assertIn("listing", shortcut["description"])
        self.assertIn("buying", shortcut["description"])

    def test_shell_cache_bumps_for_shortcut_metadata(self):
        listing = next(item for item in MANIFEST["shortcuts"] if item["short_name"] == "Listing")
        self.assertEqual(listing["url"], "/?pwa_action=transaction_start&workflow=sale_listing")
        buying = next(item for item in MANIFEST["shortcuts"] if item["short_name"] == "Buying")
        self.assertEqual(buying["url"], "/?pwa_action=transaction_start&workflow=purchase")
        lease_rep = next(item for item in MANIFEST["shortcuts"] if item["short_name"] == "Lease Rep")
        self.assertEqual(lease_rep["url"], "/?pwa_action=transaction_start&workflow=lease_representation")
        self.assertIn("homeofferflow-shell-v45", SERVICE_WORKER)


if __name__ == "__main__":
    unittest.main()
