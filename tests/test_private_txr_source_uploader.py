import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "upload_private_txr_sources", ROOT / "scripts" / "upload_private_txr_sources.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class PrivateTxrSourceUploaderTests(unittest.TestCase):
    def test_brokerage_selection_requires_a_unique_explicit_target(self):
        brokerages = [{"id": "one", "slug": "ondemand", "name": "OnDemand Realty"}]
        self.assertEqual(module._select_brokerage(brokerages, None, "ondemand")["id"], "one")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            module._select_brokerage(brokerages, "one", "ondemand")
        with self.assertRaisesRegex(ValueError, "uniquely"):
            module._select_brokerage([], None, "ondemand")

    def test_dry_run_verifies_inventory_and_never_posts_pdfs(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for expected in module.EXPECTED.values():
                (directory / expected["filename"]).write_bytes(b"private-pdf")

            def fake_request(_base, _token, method, path, _payload=None):
                if method == "GET" and "platform_source_brokerages" in path:
                    return 200, {"brokerages": [{"id": "b1", "slug": "ondemand", "name": "OnDemand Realty"}]}
                raise AssertionError("dry-run must not POST source PDFs")

            with patch.object(module, "verify", return_value=[{"ok": True}] * 4), patch.object(module, "_request", side_effect=fake_request):
                self.assertEqual(module.main([str(directory), "--access-token", "token", "--brokerage-slug", "ondemand", "--dry-run"]), 0)

    def test_inventory_only_needs_no_token_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for expected in module.EXPECTED.values():
                (directory / expected["filename"]).write_bytes(b"private-pdf")

            with patch.object(module, "verify", return_value=[{"ok": True}] * 4), patch.object(module, "_request", side_effect=AssertionError("inventory-only must not call the API")):
                self.assertEqual(module.main([str(directory), "--inventory-only"]), 0)


if __name__ == "__main__":
    unittest.main()
