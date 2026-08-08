import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_authenticated_release_qa.py"
spec = importlib.util.spec_from_file_location("run_authenticated_release_qa", SCRIPT)
qa = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "scripts"))
spec.loader.exec_module(qa)


class AuthenticatedReleaseQaTests(unittest.TestCase):
    def test_parse_clients(self):
        self.assertEqual(qa._parse_clients("1, 2, 1"), [1, 2])
        with self.assertRaises(ValueError):
            qa._parse_clients("3")

    def test_run_writes_metadata_only_bundle_and_never_signs(self):
        def fake_admin_get(base_url, token):
            return 200, {
                "brokerage": {"slug": "ondemand", "name": "OnDemand Realty"},
                "metrics": {key: 0 for key in ("memberCount", "activeMemberCount", "agentSeatCount", "offerCount", "signedCount")},
                "privacy": {
                    "buyerDetailsIncluded": False,
                    "propertyDetailsIncluded": False,
                    "offerTermsIncluded": False,
                    "documentContentsIncluded": False,
                },
                "agents": [],
                "sourceReadiness": [
                    {"formCode": "TXR-1506", "readyForRestrictedDraft": True},
                ],
            }

        def fake_request(base_url, token, path, *, method="GET", body=None):
            if method == "POST":
                return 200, "application/json", json.dumps({"agreement": {"id": "draft-1"}}).encode()
            if "preview_agreement=" in path:
                return 200, "application/pdf", b"%PDF-1.7 qa"
            return 200, "application/json", json.dumps({
                "sourceReadiness": [
                    {"formCode": "TXR-1506", "readyForRestrictedDraft": True},
                ],
            }).encode()

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(qa.admin_qa, "_get", fake_admin_get), patch.object(qa.txr_qa, "_request", fake_request):
            report = qa.run("https://example.test", "token", Path(temp_dir), ["TXR-1506"], [1])
            self.assertTrue(report["ok"])
            self.assertFalse(report["signing_sent"])
            self.assertEqual(report["txr_previews"][0]["signer_plan"], "consumers_and_associate")
            summary = json.loads((Path(temp_dir) / "authenticated-release-qa-summary.json").read_text())
            self.assertFalse(summary["signing_sent"])

    def test_release_runner_exposes_optional_visual_rendering(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("--render-pages", source)
        self.assertIn("render_manifest", source)
        self.assertIn("render_pages=args.render_pages", source)


if __name__ == "__main__":
    unittest.main()
