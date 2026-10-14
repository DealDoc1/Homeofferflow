import asyncio
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from lib.offer_reporting import offer_status_bucket, reporting_bucket, signing_summary

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("progress_admin", ROOT / "api/admin-dashboard.py")
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)


class OfferReportingProgressTests(unittest.TestCase):
    def test_actual_broker_checklist_uses_sending_not_completed_signature_as_its_milestone(self):
        if not shutil.which('node'):
            self.skipTest('Node runtime unavailable')
        result = subprocess.run(['node', '--test', str(ROOT/'tests/brokerage_signing_checklist.runtime.cjs')],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_exact_completion_aliases_are_distinct_from_signer_progress(self):
        for status in ("Completed", "complete", "buyer_signatures_complete", "document-completed", "Buyer Signed", "Fully Signed"):
            with self.subTest(status=status):
                self.assertEqual(reporting_bucket({"signwell_status": status}), "signed")
        for status in ("signed", "document_signed", "Partially Signed", "Partially Buyer Signed", "Pending", "in_progress"):
            with self.subTest(status=status):
                self.assertEqual(reporting_bucket({"status": "Signed", "signwell_status": status}), "partial")

    def test_legacy_main_signed_status_is_preserved_without_provider_conflict(self):
        self.assertEqual(reporting_bucket({"status": "Signed"}), "signed")
        self.assertEqual(reporting_bucket({"status": "Signed", "signwell_status": "  "}), "signed")
        self.assertEqual(reporting_bucket({"status": "Partially Buyer Signed"}), "partial")

    def test_unknown_and_terminal_provider_statuses_never_inherit_a_signed_main_status(self):
        for status in ("unsigned", "not signed", "sent_failed", "not sent", "Declined", "Expired", "Cancelled", "Bounced", "Error", "future_signed_review"):
            with self.subTest(status=status):
                self.assertEqual(reporting_bucket({"status": "Signed", "signwell_status": status}), "other")
                self.assertEqual(signing_summary([{"status": "Signed", "signwell_status": status}]),
                                 {"signedCount": 0, "awaitingCount": 0, "signingStartedCount": 0})

    def test_created_and_generated_drafts_are_not_sent(self):
        for status in ("Draft", "created", "Generated", "Saved", "Draft - not sent"):
            with self.subTest(status=status):
                self.assertEqual(offer_status_bucket(status), "draft")
                self.assertEqual(signing_summary([{"signwell_status": status}])["signingStartedCount"], 0)

    def test_sent_viewed_and_partial_packets_remain_awaiting_completion(self):
        rows = [{"signwell_status": s} for s in ("Awaiting Buyer Signature", "shared", "viewed", "pending", "completed")]
        self.assertEqual(signing_summary(rows), {"signedCount": 1, "awaitingCount": 4, "signingStartedCount": 5})

    def test_read_only_current_ondemand_status_distribution_has_two_not_three_completed_offers(self):
        groups = [("Expired", "Expired", 9), ("Draft", None, 9),
                  ("Generated", "Awaiting Buyer Signature", 2),
                  ("Signed", "Buyer Signatures Complete", 2), ("Generated", None, 2),
                  ("Partially Buyer Signed", "Partially Signed", 1), ("Generated", "Pending", 1)]
        rows = [{"status": status, "signwell_status": provider} for status, provider, count in groups for _ in range(count)]
        self.assertEqual(len(rows), 26)
        self.assertEqual(signing_summary(rows), {"signedCount": 2, "awaitingCount": 4, "signingStartedCount": 6})

    def test_brokerage_payload_and_agent_activity_use_the_same_safe_classification(self):
        user_id = "11111111-1111-4111-8111-111111111111"
        rows = [{"user_id": user_id, "status": "Signed", "signwell_status": status,
                 "buyer_name": "PRIVATE BUYER", "property_address": "PRIVATE ADDRESS", "document_contents": "PRIVATE DOCUMENT"}
                for status in ("completed", "signed", "Partially Signed", "Viewed", "Awaiting Buyer Signature", "unsigned")]
        async def optional(query):
            return rows if query.startswith("hof_offers?") else []
        context = {"brokerage": {"id": "22222222-2222-4222-8222-222222222222", "name": "Test Brokerage"}}
        members = [{"user_id": user_id, "role": "agent", "status": "active"}]
        with patch.object(admin, "_get", new=AsyncMock(return_value=members)), patch.object(admin, "_get_optional", new=optional):
            result = asyncio.run(admin._brokerage_dashboard_payload(context))
        self.assertEqual(result["metrics"]["signedCount"], 1)
        self.assertEqual(result["metrics"]["awaitingCount"], 4)
        self.assertEqual(result["metrics"]["signingStartedCount"], 5)
        self.assertEqual(result["agents"][0]["activity"]["signedCount"], 1)
        self.assertEqual(result["agents"][0]["activity"]["awaitingCount"], 4)
        serialized = json.dumps(result)
        for private in ("PRIVATE BUYER", "PRIVATE ADDRESS", "PRIVATE DOCUMENT"):
            self.assertNotIn(private, serialized)
        self.assertFalse(result["privacy"]["buyerDetailsIncluded"])

    def test_platform_and_brokerage_metrics_share_one_read_only_summary(self):
        source = (ROOT / "api/admin-dashboard.py").read_text()
        self.assertEqual(source.count("**_offer_signing_summary(offers)"), 2)
        self.assertNotIn('if "signed" in status:', source)
        self.assertIn("&deleted_at=is.null&select=user_id,status,signwell_status,created_at,updated_at", source)
        self.assertNotIn("signwell_document_id,created_at", source.split("async def _brokerage_dashboard_payload", 1)[1].split("async def ", 1)[0])


if __name__ == "__main__":
    unittest.main()
