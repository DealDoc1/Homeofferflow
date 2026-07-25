import json
import os
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
ADMIN_EMAILS = {
    email.strip().lower()
    for email in (os.environ.get("ADMIN_EMAILS") or os.environ.get("HOF_ADMIN_EMAILS") or "").split(",")
    if email.strip()
}
DEFAULT_ADMIN_EMAILS = {"andrew@ondemanddfw.com", "andrewchri@gmail.com", "support@homeofferflow.com"}
ALLOWED_STATUSES = {"new", "contacted", "qualified", "waitlist", "converted", "declined"}
MAX_BODY_BYTES = 12_000


def _send(handler, status, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _service_headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _parse_update_payload(data):
    lead_id = str(data.get("lead_id") or "").strip()
    status = str(data.get("status") or "").strip().lower()
    try:
        lead_id = str(uuid.UUID(lead_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("A valid partner lead ID is required.")
    if status not in ALLOWED_STATUSES:
        raise ValueError("Choose a valid partner lead status.")
    return lead_id, status


def _verified_user(auth_header):
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=12) as client:
        response = client.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
    if response.status_code != 200:
        return None
    payload = response.json()
    if not payload.get("id") or not payload.get("email"):
        return None
    return {"id": str(payload["id"]), "email": str(payload["email"]).strip().lower()}


def _is_platform_admin(user):
    if not user:
        return False
    allowed = ADMIN_EMAILS or DEFAULT_ADMIN_EMAILS
    if user["email"] in allowed:
        return True
    with httpx.Client(timeout=12) as client:
        response = client.get(
            f"{SUPABASE_URL}/rest/v1/hof_platform_admins?user_id=eq.{user['id']}&select=user_id&limit=1",
            headers=_service_headers(),
        )
    if response.status_code >= 300:
        return False
    return bool(response.json())


def _update_lead(lead_id, status):
    payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    with httpx.Client(timeout=12) as client:
        response = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{lead_id}",
            headers=_service_headers(),
            json=payload,
        )
    if response.status_code >= 300:
        raise RuntimeError("Could not update the partner lead.")
    rows = response.json() if response.text else []
    if not isinstance(rows, list) or not rows:
        raise ValueError("Partner lead was not found.")
    return rows[0]


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _send(self, 204, {})

    def do_POST(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return _send(self, 500, {"error": "Supabase env vars missing"})
        try:
            user = _verified_user(self.headers.get("authorization", ""))
            if not user:
                return _send(self, 401, {"error": "A valid signed-in session is required."})
            if not _is_platform_admin(user):
                return _send(self, 403, {"error": "Admin access is not enabled for this account."})

            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_BODY_BYTES:
                return _send(self, 400, {"error": "Invalid request size."})
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            lead_id, status = _parse_update_payload(data)
            row = _update_lead(lead_id, status)
            return _send(self, 200, {"ok": True, "lead": row})
        except ValueError as exc:
            return _send(self, 400, {"error": str(exc)[:300]})
        except json.JSONDecodeError:
            return _send(self, 400, {"error": "Invalid JSON."})
        except Exception as exc:
            print("Admin partner lead update error:", str(exc))
            return _send(self, 500, {"error": "Could not update the partner lead."})
