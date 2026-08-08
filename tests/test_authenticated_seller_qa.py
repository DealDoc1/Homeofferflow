import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_authenticated_seller_qa as runner
from scripts.validate_authenticated_seller_qa import errors_for_summary


class AuthenticatedSellerQaTests(unittest.TestCase):
    def test_parse_sellers_deduplicates_and_rejects_invalid_counts(self):
        self.assertEqual(runner._parse_sellers("2,1,2"), [2, 1])
        with self.assertRaises(ValueError):
            runner._parse_sellers("3")

    def test_validator_accepts_one_and_two_seller_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reports = []
            for count in (1, 2):
                pdf = root / f"trec-55-1-{count}-seller-private-preview.pdf"
                pdf.write_bytes(b"%PDF-1.7 private qa")
                report = {
                    "ok": True,
                    "form_code": "TREC-55-1",
                    "client_count": count,
                    "seller_review_only": True,
                    "water_source_attached": True,
                    "draft_id_present": True,
                    "preview_pdf": str(pdf),
                    "signing_sent": False,
                }
                reports.append(report)
            summary = root / "authenticated-seller-qa-summary.json"
            summary.write_text(
                json.dumps({
                    "ok": True,
                    "form_code": "TREC-55-1",
                    "water_form_code": "TREC-61-0",
                    "reports": reports,
                    "signing_sent": False,
                }),
                encoding="utf-8",
            )
            self.assertEqual(errors_for_summary(summary), [])

    def test_validator_rejects_signing_side_effect(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = Path(temp_dir) / "summary.json"
            summary.write_text(
                json.dumps({
                    "ok": True,
                    "form_code": "TREC-55-1",
                    "water_form_code": "TREC-61-0",
                    "reports": [],
                    "signing_sent": True,
                }),
                encoding="utf-8",
            )
            errors = errors_for_summary(summary)
            self.assertIn("signing_sent must be false", errors)

    def test_runner_exposes_render_pages_without_signing(self):
        source = (runner.__file__ and Path(runner.__file__).read_text())
        self.assertIn("--render-pages", source)
        self.assertIn("render_pages=render_pages", source)

    def test_seller_source_preflight_requires_both_approved_sources(self):
        ready = {
            "sourceReadiness": [
                {"formCode": "TREC-55-1", "readyForRestrictedDraft": True},
                {"formCode": "TREC-61-0", "readyForRestrictedDraft": True},
            ]
        }
        with patch.object(
            runner.qa,
            "_request",
            return_value=(200, "application/json", json.dumps(ready).encode()),
        ):
            runner._assert_seller_sources_ready("https://example.test", "token")

        incomplete = {
            "sourceReadiness": [
                {"formCode": "TREC-55-1", "readyForRestrictedDraft": True},
            ]
        }
        with patch.object(
            runner.qa,
            "_request",
            return_value=(200, "application/json", json.dumps(incomplete).encode()),
        ):
            with self.assertRaisesRegex(RuntimeError, "TREC-61-0"):
                runner._assert_seller_sources_ready("https://example.test", "token")


if __name__ == "__main__":
    unittest.main()
