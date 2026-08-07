import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_authenticated_release_qa import _errors_for_summary


class AuthenticatedReleaseQaValidatorTests(unittest.TestCase):
    def _bundle(self, temp_dir: str):
        root = Path(temp_dir)
        items = []
        plans = {
            "TXR-1501": "clients_and_associate",
            "TXR-1506": "consumers_and_associate",
            "TXR-1507": "clients_and_associate",
            "TXR-1508": "associate_and_clients",
        }
        for form, plan in plans.items():
            for count in (1, 2):
                pdf = root / f"{form.lower()}-{count}-client-private-preview.pdf"
                pdf.write_bytes(b"%PDF-1.7 private qa")
                report = {
                    "form_code": form,
                    "client_count": count,
                    "signer_plan": plan,
                    "draft_id_present": True,
                    "preview_pdf": str(pdf),
                    "signing_sent": False,
                }
                (root / f"{form.lower()}-{count}-client-qa-report.json").write_text(
                    json.dumps(report), encoding="utf-8"
                )
                items.append(report)
        summary = {
            "ok": True,
            "signing_sent": False,
            "brokerage_admin": {
                "privacy": {
                    "buyerDetailsIncluded": False,
                    "propertyDetailsIncluded": False,
                    "offerTermsIncluded": False,
                    "documentContentsIncluded": False,
                }
            },
            "txr_previews": items,
        }
        path = root / "authenticated-release-qa-summary.json"
        path.write_text(json.dumps(summary), encoding="utf-8")
        return path

    def test_valid_bundle_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            errors, payload = _errors_for_summary(self._bundle(temp_dir))
            self.assertEqual(errors, [])
            self.assertTrue(payload["ok"])

    def test_signing_or_privacy_failure_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._bundle(temp_dir)
            payload = json.loads(path.read_text())
            payload["signing_sent"] = True
            payload["brokerage_admin"]["privacy"]["offerTermsIncluded"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors, _ = _errors_for_summary(path)
            self.assertTrue(any("signing_sent" in error for error in errors))
            self.assertTrue(any("offerTermsIncluded" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
