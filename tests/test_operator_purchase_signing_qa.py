import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from lib import purchase_signing_qa as qa
from scripts.qa.purchase_signing_check import build_packet, layout_fingerprint

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("admin_operator_purchase_qa", ROOT / "api/admin-dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
USER = {"id": "d36ed4b3-7179-4b56-99c4-a709b1b847cb", "email": "andrewchri@gmail.com"}
DOCUMENT_ID = "574177e8-b381-45c8-a7ec-e3fe71b0d22b"
SCENARIO = [{"id": "807eba14-0ebc-4d0a-96c6-e5ddd69a5b02"}]


def response(code, value):
    return SimpleNamespace(status_code=code, json=lambda: value)


class OperatorPurchaseSigningQATests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = AsyncMock()
        self.client.__aenter__.return_value = self.client
        self.patches = [patch.object(MODULE, "SIGNWELL_ENABLED", True),
                        patch.object(MODULE, "SIGNWELL_API_KEY", "PRIVATE_KEY"),
                        patch.object(MODULE, "_is_platform_admin", AsyncMock(return_value=True)),
                        patch.object(MODULE, "_get", AsyncMock(side_effect=[SCENARIO, []])),
                        patch.object(MODULE, "_patch", AsyncMock()),
                        patch.object(MODULE.httpx, "AsyncClient", return_value=self.client),
                        patch.object(qa, "build_packet", return_value=(b"synthetic", [[{"type": "signature"}]], []))]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    async def test_one_reserved_attempt_uses_only_fixed_nonbinding_payload(self):
        self.client.post.side_effect = [response(201, [{"id": "run-one"}]),
                                       response(201, {"id": DOCUMENT_ID, "test_mode": True, "status": "sent",
                                                      "embedded_signing_url": "SECRET_LINK"})]
        result = await MODULE._purchase_signing_qa(USER, send=True)
        self.assertEqual(result["phase"], "created")
        self.assertEqual(result["document_id"], DOCUMENT_ID)
        calls = self.client.post.call_args_list
        self.assertIn("/rest/v1/hof_qa_runs", calls[0].args[0])
        claim = calls[0].kwargs["json"]
        self.assertEqual(claim["release_name"], qa.QA_REVISION)
        self.assertEqual(claim["status"], "running")
        self.assertEqual(json.loads(claim["notes"])["phase"], "started")
        payload = calls[1].kwargs["json"]
        self.assertIs(payload["test_mode"], True)
        self.assertIs(payload["apply_signing_order"], False)
        self.assertIs(payload["reminders"], False)
        self.assertIs(payload["with_signature_page"], False)
        self.assertEqual({r["email"] for r in payload["recipients"]},
                         {"andrewchri@gmail.com", "brewbqinfo@gmail.com"})
        self.assertEqual(MODULE._patch.call_args.args[0], "hof_qa_runs")
        self.assertNotIn("PRIVATE_KEY", str(result) + str(MODULE._patch.call_args))
        self.assertNotIn("SECRET_LINK", str(result) + str(MODULE._patch.call_args))

    async def test_recorded_attempt_never_sends_again_even_after_timeout(self):
        MODULE._get.side_effect = [SCENARIO, [{"id": "run-one", "notes": json.dumps({"qa_revision": qa.QA_REVISION, "phase": "started"})}]]
        result = await MODULE._purchase_signing_qa(USER, send=True)
        self.assertEqual(result["phase"], "started")
        self.client.post.assert_not_called()
        qa.build_packet.assert_not_called()

    async def test_concurrent_claim_loser_does_not_reach_provider(self):
        self.client.post.return_value = response(409, {})
        MODULE._get.side_effect = [SCENARIO, [], [{"id": "winner", "notes": json.dumps({"qa_revision": qa.QA_REVISION, "phase": "started"})}]]
        result = await MODULE._purchase_signing_qa(USER, send=True)
        self.assertEqual(result["run_id"], "winner")
        self.assertEqual(self.client.post.await_count, 1)

    async def test_failed_reservation_never_reaches_provider(self):
        for code, body in [(500, {}), (201, [])]:
            with self.subTest(code=code):
                MODULE._get.side_effect = [SCENARIO, []]
                self.client.post.reset_mock()
                self.client.post.return_value = response(code, body)
                with self.assertRaises(ValueError):
                    await MODULE._purchase_signing_qa(USER, send=True)
                self.assertEqual(self.client.post.await_count, 1)

    async def test_ambiguous_provider_call_is_redacted_and_not_retried(self):
        self.client.post.side_effect = [response(201, [{"id": "run-one"}]), httpx.ReadTimeout("PRIVATE_KEY SECRET_LINK")]
        result = await MODULE._purchase_signing_qa(USER, send=True)
        self.assertEqual(result["phase"], "unconfirmed")
        self.assertEqual(self.client.post.await_count, 2)
        notes = json.loads(MODULE._patch.call_args.args[2]["notes"])
        self.assertEqual(notes["error_type"], "ReadTimeout")
        self.assertNotIn("PRIVATE_KEY", str(result) + str(notes))

    async def test_provider_missing_test_mode_never_claims_confirmed_creation(self):
        self.client.post.side_effect = [response(201, [{"id": "run-one"}]), response(201, {"id": DOCUMENT_ID, "test_mode": False})]
        result = await MODULE._purchase_signing_qa(USER, send=True)
        self.assertEqual(result["phase"], "unconfirmed")
        self.assertEqual(result["document_id"], DOCUMENT_ID)
        self.assertFalse(result["test_mode"])

    async def test_receipt_write_failure_retains_claim_and_does_not_retry(self):
        self.client.post.side_effect = [response(201, [{"id": "run-one"}]), response(201, {"id": DOCUMENT_ID, "test_mode": True})]
        MODULE._patch.side_effect = RuntimeError("private upstream response")
        result = await MODULE._purchase_signing_qa(USER, send=True)
        self.assertEqual(self.client.post.await_count, 2)
        self.assertIn("could not be saved", result["message"])
        self.assertEqual(result["document_id"], DOCUMENT_ID)

    async def test_non_owner_admin_cannot_run_or_read_qa(self):
        for user in [None, {**USER, "email": "other-admin@example.test"}]:
            with self.assertRaises(PermissionError):
                await MODULE._purchase_signing_qa(user, send=True)
        MODULE._get.assert_not_called()
        self.client.post.assert_not_called()

    async def test_non_admin_owner_cannot_send(self):
        MODULE._is_platform_admin.return_value = False
        with self.assertRaises(PermissionError):
            await MODULE._purchase_signing_qa(USER, send=True)
        self.client.post.assert_not_called()

    async def test_status_is_read_only_and_completion_is_not_visual_pass(self):
        MODULE._get.side_effect = [SCENARIO, [{"id": "run-one", "notes": json.dumps({"qa_revision": qa.QA_REVISION, "phase": "created", "document_id": DOCUMENT_ID, "test_mode": True})}]]
        self.client.get.return_value = response(200, {"id": DOCUMENT_ID, "test_mode": True,
            "name": "QA ONLY - purchase placement - ee90d4d", "metadata": {"qa_revision": qa.QA_REVISION},
            "recipients": list(qa.QA_RECIPIENTS), "status": "completed"})
        result = await MODULE._purchase_signing_qa(USER)
        self.assertEqual(result["provider_status"], "completed")
        self.assertIn("still needs visual review", result["message"])
        self.client.post.assert_not_called()
        MODULE._patch.assert_not_called()

    async def test_status_rejects_foreign_document(self):
        MODULE._get.side_effect = [SCENARIO, [{"id": "run-one", "notes": json.dumps({"qa_revision": qa.QA_REVISION, "phase": "created", "document_id": DOCUMENT_ID})}]]
        self.client.get.return_value = response(200, {"id": DOCUMENT_ID, "test_mode": False, "status": "completed"})
        result = await MODULE._purchase_signing_qa(USER)
        self.assertNotEqual(result["provider_status"], "completed")
        self.assertIn("did not match", result["message"])

    async def test_provider_status_casing_and_terminal_states_are_reported_correctly(self):
        cases = [
            ("Completed", "completed", "still needs visual review"),
            (" completed ", "completed", "still needs visual review"),
            ("Sent", "sent", "awaiting completion"),
            ("Cancelled", "cancelled", "cancelled"),
            ("Declined", "declined", "declined"),
            ("Expired", "expired", "expired"),
            ("https://example.test/PRIVATE_SIGNER_LINK", "unknown", "status is unavailable"),
        ]
        for raw, expected, message in cases:
            with self.subTest(raw=raw):
                MODULE._get.side_effect = [SCENARIO, [{"id": "run-one", "notes": json.dumps({
                    "qa_revision": qa.QA_REVISION, "phase": "created", "document_id": DOCUMENT_ID,
                    "test_mode": True,
                })}]]
                self.client.get.return_value = response(200, {
                    "id": DOCUMENT_ID, "test_mode": True,
                    "name": "QA ONLY - purchase placement - ee90d4d", "metadata": {"qa_revision": qa.QA_REVISION},
                    "recipients": list(qa.QA_RECIPIENTS), "status": raw,
                })
                result = await MODULE._purchase_signing_qa(USER)
                self.assertEqual(result["provider_status"], expected)
                self.assertIn(message, result["message"])
                self.assertNotIn("PRIVATE_SIGNER_LINK", str(result))
                self.client.post.assert_not_called()
                MODULE._patch.assert_not_called()

    def test_route_is_platform_admin_only_and_has_no_custom_input(self):
        source = (ROOT / "api/admin-dashboard.py").read_text()
        action = source.index('if data.get("action") in {"send_purchase_signing_test", "check_purchase_signing_test"}')
        self.assertLess(source.index('if not asyncio.run(_is_platform_admin(user)):', source.index('def do_POST')), action)
        self.assertIn('if set(data) != {"action"}', source[action:action + 500])


class OperatorPurchaseSpecimenTests(unittest.TestCase):
    def test_runtime_builder_has_no_test_imports_and_retains_reviewed_layout(self):
        self.assertNotIn("from tests", (ROOT / "lib/purchase_signing_qa.py").read_text())
        packet, fields, cases = build_packet()
        self.assertEqual(layout_fingerprint(packet, fields, cases),
                         "f9f006620d97dccce36b273f52544788d7c664e453b199d98e74e694d9cbaf34")
        self.assertNotIn("buyer@example.com", str(qa.qa_offer()))
        self.assertEqual(qa.qa_offer()["address"], "100 QA Example Lane")
