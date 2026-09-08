import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "api" / "fill-pdf.py"


def load_offer_api():
    spec = importlib.util.spec_from_file_location("homeofferflow_paragraph4_api_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, status_code, *, payload=None, content=b""):
        self.status_code = status_code
        self._payload = payload
        self.content = content

    def json(self):
        return self._payload


class Paragraph4SourceHydrationTests(unittest.TestCase):
    def test_released_source_is_loaded_server_side_and_only_revision_is_persistable(self):
        api = load_offer_api()
        api.SUPABASE_URL = "https://example.supabase.co"
        api.SUPABASE_SERVICE_ROLE_KEY = "service-key"
        offer = {"leases": "yes", "leaseResidential": "yes"}
        responses = [
            FakeResponse(200, payload=[{
                "id": "source-id",
                "source_revision": "2026-06-15",
                "storage_bucket": "brokerage-form-sources",
                "storage_path": "private/TXR1953.pdf",
                "updated_at": "2026-09-08T00:00:00Z",
            }]),
            FakeResponse(200, content=b"%PDF-private-source"),
        ]
        with patch.object(api.httpx, "get", side_effect=responses) as get:
            api.hydrate_paragraph4_sources(offer)

        self.assertEqual(offer["paragraph4SourceRevisions"], {"TXR-1953": "2026-06-15"})
        self.assertEqual(offer["_paragraph4_source_pdf_bytes"]["TXR-1953"], b"%PDF-private-source")
        self.assertNotIn("storage_path", json.dumps(offer["paragraph4SourceRevisions"]))
        self.assertEqual(get.call_count, 2)

    def test_no_source_lookup_occurs_when_no_paragraph4_addendum_is_selected(self):
        api = load_offer_api()
        offer = {"leases": "no"}
        with patch.object(api.httpx, "get") as get:
            self.assertIs(api.hydrate_paragraph4_sources(offer), offer)
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
