import json
import os
from http.server import BaseHTTPRequestHandler

import httpx


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE")
    or os.environ.get("SUPABASE_SERVICE_KEY")
    or ""
)
MAX_BODY_BYTES = 12_000
MAX_MESSAGE_LENGTH = 4_000
MAX_CONTEXT_LENGTH = 500
ALLOWED_ISSUE_TYPES = {
    "bug",
    "pdf_field",
    "signwell",
    "missing_addendum",
    "billing",
    "crm_data",
    "ai_review",
    "suggestion",
    "other",
}
ALLOWED_ROLES = {"agent", "investor", "homebuyer", "broker", "brokerage_admin"}
AI_CALIBRATION_SCENARIOS = {
    "AI-CAL-01",
    "AI-CAL-02",
    "AI-CAL-03",
    "AI-CAL-04",
    "AI-CAL-05",
}


def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _clean(value, limit):
    return " ".join(str(value or "").split())[:limit]


def _auth_token(handler):
    header = str(handler.headers.get("Authorization") or "")
    if not header.lower().startswith("bearer "):
        return ""
    return header.split(" ", 1)[1].strip()


def _verified_user(token):
    if not token or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    response = httpx.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {token}"},
        timeout=12,
    )
    if response.status_code != 200:
        return None
    data = response.json()
    if not data.get("id") or not data.get("email"):
        return None
    return {"id": str(data["id"]), "email": str(data["email"]).strip().lower()}


def _parse_payload(raw):
    if len(raw) > MAX_BODY_BYTES:
        raise ValueError("Feedback payload is too large.")
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("Feedback payload must be valid JSON.")
    if not isinstance(payload, dict):
        raise ValueError("Feedback payload must be an object.")

    issue_type = _clean(payload.get("issueType") or payload.get("issue_type") or "other", 40)
    if issue_type not in ALLOWED_ISSUE_TYPES:
        raise ValueError("Choose a valid feedback issue type.")
    message = str(payload.get("message") or "").strip()
    if not message:
        raise ValueError("Feedback message is required.")
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError("Feedback message is too long.")
    if issue_type == "ai_review" and payload.get("anonymized") is not True:
        raise ValueError("AI calibration feedback must be anonymized before submission.")
    calibration_scenario = _clean(
        payload.get("calibrationScenario") or payload.get("calibration_scenario"),
        20,
    ) or None
    if issue_type == "ai_review" and calibration_scenario not in AI_CALIBRATION_SCENARIOS:
        raise ValueError("Choose one of the five documented AI calibration scenarios.")
    if issue_type != "ai_review":
        calibration_scenario = None
    role = _clean(payload.get("role"), 40).lower()
    if role not in ALLOWED_ROLES:
        role = "agent"
    return {
        "issue_type": issue_type,
        "calibration_scenario": calibration_scenario,
        "message": message,
        "role": role,
        "page_url": _clean(payload.get("pageUrl") or payload.get("page_url"), MAX_CONTEXT_LENGTH),
        "user_agent": _clean(payload.get("userAgent") or payload.get("user_agent"), MAX_CONTEXT_LENGTH),
    }


def _save_feedback(user, feedback):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Feedback storage is not configured.")
    response = httpx.post(
        f"{SUPABASE_URL}/rest/v1/hof_feedback",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        json={
            "user_id": user["id"],
            "email": user["email"],
            "issue_type": feedback["issue_type"],
            "calibration_scenario": feedback["calibration_scenario"],
            "message": feedback["message"],
            "role": feedback["role"],
            "page_url": feedback["page_url"],
            "user_agent": feedback["user_agent"],
            "status": "new",
        },
        timeout=12,
    )
    if response.status_code >= 300:
        raise RuntimeError("Feedback could not be saved.")
    rows = response.json() if response.text else []
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Feedback was not returned after saving.")
    row = rows[0]
    return {
        "id": row.get("id"),
        "created_at": row.get("created_at"),
        "issue_type": row.get("issue_type"),
        "calibration_scenario": row.get("calibration_scenario"),
        "message": row.get("message"),
        "role": row.get("role"),
        "email": user["email"],
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json(self, 204, {})

    def do_GET(self):
        _json(self, 405, {"error": "Use POST to submit feedback."})

    def do_POST(self):
        try:
            user = _verified_user(_auth_token(self))
            if not user:
                _json(self, 401, {"error": "Sign in before sending feedback."})
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY_BYTES:
                _json(self, 413, {"error": "Feedback payload is too large."})
                return
            payload = self.rfile.read(length)
            feedback = _parse_payload(payload)
            saved = _save_feedback(user, feedback)
            _json(self, 201, {"ok": True, "feedback": saved})
        except ValueError as exc:
            _json(self, 400, {"error": str(exc)})
        except Exception as exc:
            print("Feedback submission failed:", str(exc)[:300])
            _json(self, 500, {"error": "Feedback could not be saved."})
