"""Authenticated agent-owned IABS metadata API."""
import asyncio
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_iabs_profile_admin", ROOT / "api" / "admin-dashboard.py")
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)

OWNER = "11111111-1111-4111-8111-111111111111"
USER = {"id": OWNER, "email": "agent@example.test"}
ROW = {"id": "iabs-row", "user_id": OWNER, "document_type": "iabs",
       "storage_bucket": "agent-documents", "storage_path": f"{OWNER}/iabs.pdf",
       "original_filename": "Brokerage IABS.pdf", "mime_type": "application/pdf",
       "byte_size": 2048, "updated_at": "2026-10-29T12:00:00Z"}


class FakeResponse:
    status_code = 204
    text = ""


class FakeClient:
    def __init__(self):
        self.post = AsyncMock(return_value=FakeResponse())
        self.delete = AsyncMock(return_value=FakeResponse())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


class AgentIabsProfileApiTests(unittest.TestCase):
    def test_upload_token_is_issued_only_for_the_fixed_private_owner_pdf_path(self):
        client = FakeClient()
        response = type("SignedResponse", (), {
            "status_code": 200, "text": '{"token":"short-lived-upload-token"}',
            "json": lambda self: {"token": "short-lived-upload-token"},
        })()
        client.post = AsyncMock(return_value=response)
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": OWNER, "role": "agent"}])), \
                patch.object(API.httpx, "AsyncClient", return_value=client), \
                patch.object(API, "SUPABASE_URL", "https://private.example"), \
                patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"):
            result = asyncio.run(API._prepare_agent_iabs_upload(USER, {
                "action": "prepare_agent_iabs_upload", "content_type": "application/pdf",
                "size_bytes": 2048,
            }))
        self.assertEqual(result, {"bucket": "agent-documents", "path": f"{OWNER}/iabs.pdf",
                                  "token": "short-lived-upload-token"})
        url, = client.post.await_args.args
        self.assertIn(f"/storage/v1/object/upload/sign/agent-documents/{OWNER}/iabs.pdf", url)
        self.assertEqual(client.post.await_args.kwargs["headers"]["x-upsert"], "true")
        self.assertEqual(client.post.await_args.kwargs["json"], {})
        self.assertEqual(client.post.await_args.kwargs["headers"]["Authorization"], "Bearer service-role")

    def test_upload_token_rejects_non_agent_and_invalid_or_extra_claims_before_storage(self):
        client = FakeClient()
        for role in ("investor", "partner"):
            with self.subTest(role=role), \
                    patch.object(API, "_get", AsyncMock(return_value=[{"id": OWNER, "role": role}])), \
                    patch.object(API.httpx, "AsyncClient", return_value=client):
                with self.assertRaises(PermissionError):
                    asyncio.run(API._prepare_agent_iabs_upload(USER, {
                        "action": "prepare_agent_iabs_upload", "content_type": "application/pdf", "size_bytes": 2048,
                    }))
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": OWNER, "role": "agent"}])), \
                patch.object(API.httpx, "AsyncClient", return_value=client):
            for payload in (
                {"action": "prepare_agent_iabs_upload", "content_type": "image/png", "size_bytes": 2048},
                {"action": "prepare_agent_iabs_upload", "content_type": "application/pdf", "size_bytes": True},
                {"action": "prepare_agent_iabs_upload", "content_type": "application/pdf", "size_bytes": 10485761},
                {"action": "prepare_agent_iabs_upload", "content_type": "application/pdf", "size_bytes": 2048,
                 "path": "someone-elses-file.pdf"},
            ):
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    asyncio.run(API._prepare_agent_iabs_upload(USER, payload))
        client.post.assert_not_awaited()

    def test_missing_profile_record_has_its_own_recoverable_error_type(self):
        with patch.object(API, "_get", AsyncMock(return_value=[])):
            with self.assertRaises(API.AgentIabsProfileMissing):
                asyncio.run(API._agent_iabs_profile_record(USER))

    def test_malformed_profile_record_is_not_misreported_as_missing(self):
        malformed = {**ROW, "storage_path": f"{OWNER}/unexpected.pdf"}
        with patch.object(API, "_get", AsyncMock(return_value=[malformed])):
            with self.assertRaisesRegex(ValueError, "profile record is incomplete") as error:
                asyncio.run(API._agent_iabs_profile_record(USER))
        self.assertNotIsInstance(error.exception, API.AgentIabsProfileMissing)

    def test_read_returns_only_owner_record_and_empty_profile(self):
        with patch.object(API, "_get", AsyncMock(side_effect=[
            [{"id": OWNER, "role": "agent"}], [ROW]
        ])) as get:
            self.assertEqual(asyncio.run(API._agent_iabs_profile_metadata(USER)), ROW)
            self.assertIn(f"user_id=eq.{OWNER}", get.await_args_list[1].args[0])
        with patch.object(API, "_get", AsyncMock(side_effect=[[{"id": OWNER, "role": "agent"}], []])):
            self.assertIsNone(asyncio.run(API._agent_iabs_profile_metadata(USER)))

    def test_read_rejects_non_agent_profiles(self):
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": OWNER, "role": "investor"}])):
            with self.assertRaises(PermissionError):
                asyncio.run(API._agent_iabs_profile_metadata(USER))

    def test_save_derives_owner_and_fixed_storage_fields_on_server(self):
        client = FakeClient()
        with patch.object(API, "_get", AsyncMock(side_effect=[
            [{"id": OWNER, "role": "agent"}], [ROW]
        ])), patch.object(API.httpx, "AsyncClient", return_value=client), \
                patch.object(API, "SUPABASE_URL", "https://private.example"), \
                patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "service-role"):
            result = asyncio.run(API._save_agent_iabs_profile_metadata(USER, {
                "action": "save_agent_iabs_metadata", "original_filename": "Brokerage IABS.pdf",
                "byte_size": 2048,
            }))
        self.assertEqual(result, ROW)
        args = client.post.await_args
        self.assertTrue(args.args[0].endswith("on_conflict=user_id,document_type"))
        payload = args.kwargs["json"]
        self.assertEqual(payload["user_id"], OWNER)
        self.assertEqual(payload["storage_path"], f"{OWNER}/iabs.pdf")
        self.assertEqual(payload["storage_bucket"], "agent-documents")
        self.assertEqual(payload["byte_size"], 2048)
        self.assertNotIn("spoofed", payload)

    def test_invalid_save_payload_never_writes(self):
        client = FakeClient()
        with patch.object(API, "_get", AsyncMock(return_value=[{"id": OWNER, "role": "agent"}])), \
                patch.object(API.httpx, "AsyncClient", return_value=client):
            with self.assertRaises(ValueError):
                asyncio.run(API._save_agent_iabs_profile_metadata(USER, {
                    "action": "save_agent_iabs_metadata", "original_filename": "bad.pdf",
                    "byte_size": True, "user_id": OWNER,
                }))
        client.post.assert_not_awaited()

    def test_signed_upload_http_route_authenticates_and_disables_response_caching(self):
        payload = {"action": "prepare_agent_iabs_upload", "content_type": "application/pdf", "size_bytes": 128}
        upload = {"bucket": "agent-documents", "path": f"{OWNER}/iabs.pdf", "token": "fictional-token"}
        prepare = AsyncMock(return_value=upload)
        for user in (None, USER):
            with self.subTest(authenticated=bool(user)):
                body = json.dumps(payload).encode()
                request = object.__new__(API.handler)
                request.path = "/api/admin-dashboard"
                request.headers = {"Content-Length": str(len(body)), "authorization": "Bearer fictional"}
                request.rfile, request.wfile = BytesIO(body), BytesIO()
                sent = {}
                request.send_response = lambda code: sent.update(status=code)
                request.send_header = lambda name, value: sent.update({name: value})
                request.end_headers = lambda: None
                with patch.object(API, "SUPABASE_URL", "https://private.example"), \
                        patch.object(API, "SUPABASE_SERVICE_ROLE_KEY", "fictional"), \
                        patch.object(API, "_verified_user", AsyncMock(return_value=user)), \
                        patch.object(API, "_prepare_agent_iabs_upload", prepare):
                    request.do_POST()
                self.assertEqual(sent["Cache-Control"], "no-store")
                self.assertEqual(sent["status"], 200 if user else 401)
                result = json.loads(request.wfile.getvalue())
                if user:
                    self.assertEqual(result["upload"], upload)
                    prepare.assert_awaited_once_with(USER, payload)
                else:
                    self.assertNotIn("upload", result)
                    prepare.assert_not_awaited()
