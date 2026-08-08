import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_authenticated_txr_qa_source_preflight",
    ROOT / "scripts" / "run_authenticated_txr_qa.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class AuthenticatedTXRSourcePreflightTests(unittest.TestCase):
    def test_preflight_accepts_only_explicitly_ready_sources(self):
        payload = {
            "sourceReadiness": [
                {"formCode": "TXR-1507", "readyForRestrictedDraft": True},
                {"formCode": "TXR-1501", "readyForRestrictedDraft": True},
            ]
        }
        with patch.object(module, "_request", return_value=(200, "application/json", json.dumps(payload).encode())):
            module._assert_restricted_sources_ready("https://example.test", "token", ["TXR-1507", "TXR-1501"])

    def test_preflight_fails_closed_when_any_source_is_not_ready(self):
        payload = {"sourceReadiness": [{"formCode": "TXR-1507", "readyForRestrictedDraft": True}]}
        with patch.object(module, "_request", return_value=(200, "application/json", json.dumps(payload).encode())):
            with self.assertRaisesRegex(RuntimeError, "TXR-1501"):
                module._assert_restricted_sources_ready("https://example.test", "token", ["TXR-1507", "TXR-1501"])

    def test_seller_preview_does_not_use_restricted_txr_preflight(self):
        with patch.object(module, "_request") as request:
            module._assert_restricted_sources_ready("https://example.test", "token", ["TREC-55-1"])
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
