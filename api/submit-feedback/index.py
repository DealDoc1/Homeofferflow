import json
import os
import re
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
    "brokerage_access",
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
ALLOWED_USAGE_EVENT_TYPES = {"signed_packet"}
USAGE_BILLING_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MAX_USAGE_METADATA_KEYS = 8


class UsageLimitError(ValueError):
    """A signed-packet request would exceed the account's current allowance."""

    def __init__(self, summary):
        self.summary = summary
        super().__init__("Monthly packet usage limit reached.")


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


def _authoritative_role(user):
    """Read the role from the protected profile, never from browser JSON."""
    if not user or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        response = httpx.get(
            f"{SUPABASE_URL}/rest/v1/hof_profiles"
            f"?id=eq.{user['id']}&select=role,is_brokerage_admin&limit=1",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            },
            timeout=12,
        )
        if response.status_code >= 300:
            return None
        rows = response.json()
        if not isinstance(rows, list) or not rows:
            return None
        profile = rows[0] or {}
        if profile.get("is_brokerage_admin") is True or str(profile.get("role") or "").lower() == "brokerage_admin":
            return "brokerage_admin"
        role = str(profile.get("role") or "").lower()
        return role if role in {"agent", "investor", "homebuyer"} else "agent"
    except Exception:
        return None


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


def _parse_json_object(raw):
    if len(raw) > MAX_BODY_BYTES:
        raise ValueError("Request payload is too large.")
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("Request payload must be valid JSON.")
    if not isinstance(payload, dict):
        raise ValueError("Request payload must be an object.")
    return payload


def _clean_usage_metadata(value):
    """Keep usage telemetry small and non-sensitive before it reaches storage."""
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise ValueError("Usage metadata must be an object.")
    if len(value) > MAX_USAGE_METADATA_KEYS:
        raise ValueError("Usage metadata contains too many fields.")
    clean = {}
    for key, raw in value.items():
        name = _clean(key, 40)
        if not name:
            continue
        if isinstance(raw, (str, int, float, bool)) or raw is None:
            clean[name] = _clean(raw, 160) if isinstance(raw, str) else raw
    return clean


def _parse_usage_event(payload):
    event_type = _clean(payload.get("eventType") or payload.get("event_type"), 40)
    if event_type not in ALLOWED_USAGE_EVENT_TYPES:
        raise ValueError("Choose a valid usage event type.")
    try:
        quantity = int(payload.get("quantity", 1))
    except (TypeError, ValueError):
        raise ValueError("Usage quantity must be a positive integer.")
    if quantity < 1 or quantity > 10:
        raise ValueError("Usage quantity must be between 1 and 10.")
    billing_month = _clean(payload.get("billingMonth") or payload.get("billing_month"), 7)
    if not USAGE_BILLING_MONTH_RE.fullmatch(billing_month):
        raise ValueError("Usage billing month must use YYYY-MM format.")
    offer_id = _clean(payload.get("offerId") or payload.get("offer_id"), 80) or None
    if offer_id and not re.fullmatch(r"[0-9a-fA-F-]{16,80}", offer_id):
        raise ValueError("Usage offer ID is invalid.")
    return {
        "event_type": event_type,
        "quantity": quantity,
        "billing_month": billing_month,
        "offer_id": offer_id,
        "metadata": _clean_usage_metadata(payload.get("metadata")),
    }


def _save_usage_event(user, event):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Usage storage is not configured.")
    preflight = _usage_preflight(user, event["billing_month"], event["quantity"])
    if not preflight["allowed"]:
        raise UsageLimitError(preflight)
    if event["offer_id"]:
        response = httpx.get(
            f"{SUPABASE_URL}/rest/v1/hof_offers"
            f"?id=eq.{event['offer_id']}&user_id=eq.{user['id']}&select=id&limit=1",
            headers={"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"},
            timeout=12,
        )
        if response.status_code >= 300 or not response.json():
            raise ValueError("Usage offer ID does not belong to this account.")
    response = httpx.post(
        f"{SUPABASE_URL}/rest/v1/hof_usage_events",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        json={
            "user_id": user["id"],
            "offer_id": event["offer_id"],
            "event_type": event["event_type"],
            "quantity": event["quantity"],
            "billing_month": event["billing_month"],
            "metadata": event["metadata"],
        },
        timeout=12,
    )
    if response.status_code >= 300:
        raise RuntimeError("Usage event could not be saved.")
    return {"ok": True}


def _usage_summary(user, billing_month):
    billing_month = _clean(billing_month, 7)
    if not USAGE_BILLING_MONTH_RE.fullmatch(billing_month):
        raise ValueError("Usage billing month must use YYYY-MM format.")
    response = httpx.get(
        f"{SUPABASE_URL}/rest/v1/hof_usage_events"
        f"?user_id=eq.{user['id']}&billing_month=eq.{billing_month}"
        "&event_type=eq.signed_packet&select=quantity",
        headers={"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"},
        timeout=12,
    )
    if response.status_code >= 300:
        raise RuntimeError("Usage could not be loaded.")
    rows = response.json() if response.text else []
    return {"billingMonth": billing_month, "used": sum(int(row.get("quantity") or 0) for row in rows)}


def _usage_preflight(user, billing_month, quantity=1):
    """Return an authoritative allowance before a packet is generated."""
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("Usage quantity must be a positive integer.")
    if quantity < 1 or quantity > 10:
        raise ValueError("Usage quantity must be between 1 and 10.")
    billing_month = _clean(billing_month, 7)
    if not USAGE_BILLING_MONTH_RE.fullmatch(billing_month):
        raise ValueError("Usage billing month must use YYYY-MM format.")
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Usage storage is not configured.")

    role = _authoritative_role(user) or "agent"
    response = httpx.get(
        f"{SUPABASE_URL}/rest/v1/hof_subscriptions"
        f"?user_id=eq.{user['id']}&select=status,packet_limit&limit=1",
        headers={"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"},
        timeout=12,
    )
    if response.status_code >= 300:
        raise RuntimeError("Subscription could not be loaded.")
    rows = response.json() if response.text else []
    subscription = rows[0] if isinstance(rows, list) and rows else {}
    status = str(subscription.get("status") or "beta").lower()
    default_limit = 15 if role == "investor" else 10
    try:
        limit = int(subscription.get("packet_limit") or default_limit)
    except (TypeError, ValueError):
        limit = default_limit
    limit = max(0, min(limit, 10000))
    summary = _usage_summary(user, billing_month)
    used = int(summary.get("used") or 0)
    allowed_status = status in {"beta", "trialing", "active", "free_admin"}
    allowed = allowed_status and used + quantity <= limit
    return {
        "allowed": allowed,
        "status": status,
        "billingMonth": billing_month,
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
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
                _json(self, 413, {"error": "Request payload is too large."})
                return
            payload = self.rfile.read(length)
            request = _parse_json_object(payload)
            action = _clean(request.get("action"), 40)
            if action == "usage_summary":
                summary = _usage_summary(user, request.get("billingMonth") or request.get("billing_month"))
                _json(self, 200, summary)
                return
            if action == "usage_preflight":
                summary = _usage_preflight(
                    user,
                    request.get("billingMonth") or request.get("billing_month"),
                    request.get("quantity", 1),
                )
                _json(self, 200, summary)
                return
            if action == "usage_event":
                event = _parse_usage_event(request)
                saved = _save_usage_event(user, event)
                _json(self, 201, saved)
                return
            feedback = _parse_payload(payload)
            authoritative_role = _authoritative_role(user)
            if feedback["issue_type"] == "ai_review":
                if authoritative_role not in {"agent", "brokerage_admin"}:
                    _json(self, 403, {"error": "AI calibration feedback requires an active agent or brokerage administrator profile."})
                    return
                feedback["role"] = authoritative_role
            else:
                feedback["role"] = authoritative_role or "agent"
            saved = _save_feedback(user, feedback)
            _json(self, 201, {"ok": True, "feedback": saved})
        except UsageLimitError as exc:
            _json(self, 409, {"error": str(exc), **exc.summary})
        except ValueError as exc:
            _json(self, 400, {"error": str(exc)})
        except Exception as exc:
            print("Feedback submission failed:", str(exc)[:300])
            _json(self, 500, {"error": "Feedback could not be saved."})
