"""Platform-owner intake helpers for authorized, private brokerage form sources.

This endpoint stores an exact source PDF in the existing private brokerage
source vault. It never renders, sends, signs, or activates a form. Source
approval, signer planning, completed-PDF QA, and product release remain
separate gates.
"""

import base64
import binascii
import hashlib
import json
import os
import re
import urllib.parse
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

import httpx


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE")
    or os.environ.get("SUPABASE_SERVICE_KEY")
    or ""
)
PUBLIC_APP_ORIGIN = (os.environ.get("PUBLIC_APP_URL") or "https://www.homeofferflow.com").rstrip("/")
DEFAULT_ADMIN_EMAILS = {"andrew@ondemanddfw.com", "andrewchri@gmail.com", "support@homeofferflow.com"}
ADMIN_EMAILS = {
    item.strip().lower()
    for item in (os.environ.get("ADMIN_EMAILS") or os.environ.get("HOF_ADMIN_EMAILS") or "").split(",")
    if item.strip()
}
BUCKET = "brokerage-form-sources"
MAX_SOURCE_BYTES = 10 * 1024 * 1024
MAX_BODY_BYTES = 15 * 1024 * 1024
FORM_CODES = {
    "TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508",
    "TXR-1101", "TXR-1102", "TXR-1406", "TXR-1418",
}
REVISION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,47}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _headers(content_type="application/json"):
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
    }


def _json(handler, status, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    # This endpoint handles private source PDFs and requires a signed-in
    # platform-admin bearer token. Do not advertise it to arbitrary browser
    # origins; keep the browser surface restricted to the configured app.
    handler.send_header("Access-Control-Allow-Origin", PUBLIC_APP_ORIGIN)
    handler.send_header("Vary", "Origin")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _clean(value, maximum):
    value = " ".join(str(value or "").strip().split())
    if len(value) > maximum:
        raise ValueError("A source field is too long.")
    return value


def _parse_payload(raw):
    if len(raw) > MAX_BODY_BYTES:
        raise ValueError("Source upload is too large.")
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("Source upload must be valid JSON.")
    if not isinstance(payload, dict):
        raise ValueError("Source upload must be an object.")

    form_code = _clean(payload.get("formCode"), 20)
    revision = _clean(payload.get("sourceRevision"), 48)
    filename = _clean(payload.get("originalFilename"), 180)
    brokerage_id = _clean(payload.get("brokerageId"), 80)
    expected_sha256 = _clean(payload.get("sourceSha256"), 64).lower()
    encoded = str(payload.get("contentBase64") or "").strip()
    if form_code not in FORM_CODES:
        raise ValueError("Choose a supported form source.")
    if not REVISION_RE.fullmatch(revision):
        raise ValueError("Enter the revision shown on the source form.")
    if not filename.lower().endswith(".pdf"):
        raise ValueError("The authorized source must be a PDF.")
    if not brokerage_id:
        raise ValueError("Choose a brokerage for the source.")
    if not SHA256_RE.fullmatch(expected_sha256):
        raise ValueError("The source SHA-256 fingerprint is invalid.")
    if payload.get("authorizationAttested") is not True:
        raise ValueError("Confirm that you are authorized to approve this exact source PDF.")
    if encoded.startswith("data:"):
        encoded = encoded.split(",", 1)[-1]
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("The source PDF encoding is invalid.")
    if not content or len(content) > MAX_SOURCE_BYTES:
        raise ValueError("Source PDFs must be larger than zero and 10 MB or smaller.")
    if not content.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a PDF source.")
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError("The source fingerprint does not match the uploaded PDF.")
    return {
        "form_code": form_code,
        "source_revision": revision,
        "original_filename": filename,
        "brokerage_id": brokerage_id,
        "source_sha256": actual_sha256,
        "content": content,
    }


async def _verified_user(authorization):
    token = str(authorization or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {token}"},
        )
    if response.status_code != 200:
        return None
    user = response.json()
    if not user.get("id") or not user.get("email"):
        return None
    return {"id": str(user["id"]), "email": str(user["email"]).strip().lower()}


async def _is_platform_admin(user):
    if not user:
        return False
    if user["email"] in (DEFAULT_ADMIN_EMAILS | ADMIN_EMAILS):
        return True
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/hof_platform_admins?user_id=eq.{urllib.parse.quote(user['id'])}&select=user_id&limit=1",
            headers=_headers(),
        )
    return response.status_code == 200 and bool(response.json())


async def _get_brokerage(brokerage_id):
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/hof_brokerages?" \
            f"id=eq.{urllib.parse.quote(brokerage_id)}&is_active=eq.true&select=id,name,dba_name,slug&limit=1",
            headers=_headers(),
        )
    if response.status_code != 200:
        raise RuntimeError("Could not verify the selected brokerage.")
    rows = response.json()
    if not rows:
        raise ValueError("The selected brokerage is not active.")
    return rows[0]


async def _active_brokerages(user):
    if not await _is_platform_admin(user):
        raise PermissionError("Platform-admin access is required for private source intake.")
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/hof_brokerages?is_active=eq.true&select=id,name,dba_name,slug&order=name.asc&limit=500",
            headers=_headers(),
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not load active brokerages.")
    return {
        "brokerages": [
            {"id": row.get("id"), "name": row.get("dba_name") or row.get("name"), "slug": row.get("slug")}
            for row in response.json()
        ]
    }


async def _assert_no_duplicate(brokerage_id, form_code, revision):
    query = (
        f"brokerage_id=eq.{urllib.parse.quote(brokerage_id)}"
        f"&form_code=eq.{urllib.parse.quote(form_code)}"
        f"&source_revision=eq.{urllib.parse.quote(revision)}"
        "&status=neq.retired&select=id&limit=1"
    )
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(f"{SUPABASE_URL}/rest/v1/hof_brokerage_form_sources?{query}", headers=_headers())
    if response.status_code >= 300:
        raise RuntimeError("Could not check existing brokerage sources.")
    if response.json():
        raise ValueError(f"An active {form_code} source with revision {revision} already exists.")


async def _upload_source(user, data):
    if not await _is_platform_admin(user):
        raise PermissionError("Platform-admin access is required for private source intake.")
    parsed = _parse_payload(data)
    brokerage = await _get_brokerage(parsed["brokerage_id"])
    await _assert_no_duplicate(parsed["brokerage_id"], parsed["form_code"], parsed["source_revision"])
    path = (
        f"{parsed['brokerage_id']}/{parsed['form_code']}-"
        f"{parsed['source_revision']}-{uuid.uuid4().hex}.pdf"
    )
    storage_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{urllib.parse.quote(path, safe='/') }"
    async with httpx.AsyncClient(timeout=30) as client:
        upload = await client.post(
            storage_url,
            headers={**_headers("application/pdf"), "x-upsert": "false"},
            content=parsed["content"],
        )
        if upload.status_code >= 300:
            raise RuntimeError("Could not store the private source PDF.")
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "brokerage_id": parsed["brokerage_id"],
            "form_code": parsed["form_code"],
            "source_revision": parsed["source_revision"],
            "status": "approved",
            "storage_bucket": BUCKET,
            "storage_path": path,
            "original_filename": parsed["original_filename"],
            "mime_type": "application/pdf",
            "byte_size": len(parsed["content"]),
            "source_sha256": parsed["source_sha256"],
            "authorization_attested": True,
            "authorized_by_user_id": user["id"],
            "authorized_at": now,
            "updated_at": now,
        }
        insert = await client.post(
            f"{SUPABASE_URL}/rest/v1/hof_brokerage_form_sources",
            headers={**_headers(), "Prefer": "return=representation"},
            json=record,
        )
        if insert.status_code >= 300:
            await client.delete(storage_url, headers=_headers())
            raise RuntimeError("Could not record the private source approval.")
    return {
        "id": (insert.json() or [{}])[0].get("id"),
        "brokerageId": parsed["brokerage_id"],
        "brokerageName": brokerage.get("dba_name") or brokerage.get("name"),
        "formCode": parsed["form_code"],
        "sourceRevision": parsed["source_revision"],
        "originalFilename": parsed["original_filename"],
        "sourceSha256": parsed["source_sha256"],
        "status": "approved",
        "workflowActivated": False,
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json(self, 204, {})

    def do_POST(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            _json(self, 500, {"error": "Supabase environment is not configured."})
            return
        try:
            import asyncio
            user = asyncio.run(_verified_user(self.headers.get("authorization", "")))
            if not user:
                _json(self, 401, {"error": "A valid signed-in session is required."})
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_BODY_BYTES:
                _json(self, 400, {"error": "Invalid source upload size."})
                return
            raw_payload = self.rfile.read(length)
            result = asyncio.run(_upload_source(user, raw_payload))
            _json(self, 201, {"ok": True, "source": result})
        except PermissionError as exc:
            _json(self, 403, {"error": str(exc)})
        except (ValueError, json.JSONDecodeError) as exc:
            _json(self, 400, {"error": str(exc)})
        except Exception as exc:
            print(f"Platform source upload failed: {str(exc)[:300]}")
            _json(self, 500, {"error": "Private source intake failed."})

    def do_GET(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            _json(self, 500, {"error": "Supabase environment is not configured."})
            return
        try:
            import asyncio
            user = asyncio.run(_verified_user(self.headers.get("authorization", "")))
            if not user:
                _json(self, 401, {"error": "A valid signed-in session is required."})
                return
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if str((query.get("scope") or [""])[0]).strip().lower() != "brokerages":
                _json(self, 400, {"error": "Choose a supported source-intake scope."})
                return
            _json(self, 200, asyncio.run(_active_brokerages(user)))
        except PermissionError as exc:
            _json(self, 403, {"error": str(exc)})
        except Exception as exc:
            print(f"Platform source brokerage list failed: {str(exc)[:300]}")
            _json(self, 500, {"error": "Could not load brokerages."})

    def log_message(self, *_args):
        return
