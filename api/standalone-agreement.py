import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
FORM_CODE = "TXR-1507"
MAX_CLIENTS = 2


def _json_bytes(value):
    return json.dumps(value).encode("utf-8")


def _server_headers():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase standalone-agreement configuration is unavailable.")
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def _request_json(url, method="GET", headers=None, body=None):
    request = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        try:
            return error.code, json.loads(raw)
        except json.JSONDecodeError:
            return error.code, {"message": raw}


def _bearer_token(headers):
    value = headers.get("Authorization", "")
    if value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip()
    return ""


def _authenticated_user(headers):
    token = _bearer_token(headers)
    if not token or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    status, user = _request_json(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {token}"},
    )
    return user if status == 200 and isinstance(user, dict) and user.get("id") else None


def _safe_text(value, field, max_length=400):
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{field} is required.")
    if len(value) > max_length:
        raise ValueError(f"{field} is too long.")
    return value


def _client_names(value):
    if not isinstance(value, list) or not (1 <= len(value) <= MAX_CLIENTS):
        raise ValueError("Add one or two client names.")
    return [_safe_text(name, "Each client name", 180) for name in value]


def validate_draft(payload):
    if not isinstance(payload, dict):
        raise ValueError("Agreement data is required.")
    if payload.get("formCode") != FORM_CODE:
        raise ValueError("Only TXR-1507 is available through this endpoint.")

    clients = _client_names(payload.get("clientNames"))
    market_area = _safe_text(payload.get("marketArea"), "Market area", 800)
    term_start = _safe_text(payload.get("termStart"), "Term start date", 30)
    term_end = _safe_text(payload.get("termEnd"), "Term end date", 30)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", term_start) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", term_end):
        raise ValueError("Use YYYY-MM-DD for both term dates.")

    service_level = payload.get("serviceLevel")
    if service_level not in ("full_services", "showing_services"):
        raise ValueError("Choose Full Services or Showing Services.")
    showing_fee = str(payload.get("showingFee") or "").strip()
    if service_level == "showing_services" and not showing_fee:
        raise ValueError("Showing Services requires the execution fee.")

    intermediary = payload.get("intermediary")
    if intermediary not in ("authorized", "not_authorized"):
        raise ValueError("Choose whether intermediary is authorized.")

    source_id = _safe_text(payload.get("formSourceId"), "Approved TXR-1507 source", 80)
    compensation = payload.get("compensation") or {}
    if not isinstance(compensation, dict):
        raise ValueError("Compensation data is invalid.")

    return {
        "form_source_id": source_id,
        "client_names": clients,
        "agreement_data": {
            "market_area": market_area,
            "term_start": term_start,
            "term_end": term_end,
            "service_level": service_level,
            "showing_fee": showing_fee,
            "purchase_percentage": str(compensation.get("purchasePercentage") or "").strip(),
            "purchase_flat_fee": str(compensation.get("purchaseFlatFee") or "").strip(),
            "lease_one_month_percentage": str(compensation.get("leaseOneMonthPercentage") or "").strip(),
            "lease_total_rents_percentage": str(compensation.get("leaseTotalRentsPercentage") or "").strip(),
            "lease_flat_fee": str(compensation.get("leaseFlatFee") or "").strip(),
            "intermediary": intermediary,
        },
    }


def _profile_and_membership(user_id):
    encoded_user_id = urllib.parse.quote(str(user_id))
    status, profiles = _request_json(
        f"{SUPABASE_URL}/rest/v1/hof_profiles?id=eq.{encoded_user_id}&select=id,role,brokerage_id&limit=1",
        headers=_server_headers(),
    )
    if status != 200 or not profiles or not profiles[0].get("brokerage_id"):
        raise PermissionError("An active brokerage membership is required for this agreement.")
    profile = profiles[0]
    brokerage_id = str(profile["brokerage_id"])
    status, members = _request_json(
        f"{SUPABASE_URL}/rest/v1/hof_brokerage_members?user_id=eq.{encoded_user_id}&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}&status=eq.active&select=id&limit=1",
        headers=_server_headers(),
    )
    if status != 200 or not members:
        raise PermissionError("Your brokerage membership is not active.")
    return profile, brokerage_id


def _approved_source(source_id, brokerage_id):
    status, sources = _request_json(
        f"{SUPABASE_URL}/rest/v1/hof_brokerage_form_sources?id=eq.{urllib.parse.quote(source_id)}&brokerage_id=eq.{urllib.parse.quote(brokerage_id)}&form_code=eq.{FORM_CODE}&status=eq.approved&authorization_attested=is.true&select=id,source_revision&limit=1",
        headers=_server_headers(),
    )
    if status != 200 or not sources:
        raise ValueError("Choose an approved TXR-1507 source from your brokerage.")
    return sources[0]


def create_draft(user, payload):
    draft = validate_draft(payload)
    _, brokerage_id = _profile_and_membership(user["id"])
    source = _approved_source(draft["form_source_id"], brokerage_id)
    record = {
        "brokerage_id": brokerage_id,
        "agent_user_id": user["id"],
        "form_source_id": source["id"],
        "form_code": FORM_CODE,
        "source_revision": source["source_revision"],
        "status": "draft",
        "client_names": draft["client_names"],
        "agreement_data": draft["agreement_data"],
    }
    status, result = _request_json(
        f"{SUPABASE_URL}/rest/v1/hof_standalone_agreements",
        method="POST",
        headers={**_server_headers(), "Prefer": "return=representation"},
        body=_json_bytes(record),
    )
    if status not in (200, 201) or not result:
        raise RuntimeError("Could not save the agreement draft.")
    return result[0] if isinstance(result, list) else result


class handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        encoded = _json_bytes(body)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "https://www.homeofferflow.com")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_POST(self):
        user = _authenticated_user(self.headers)
        if not user:
            return self._send(401, {"error": "Sign in before creating an agreement draft."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if payload.get("action") != "create_draft":
                raise ValueError("Unsupported agreement action.")
            draft = create_draft(user, payload)
            self._send(201, {"status": "ok", "agreement": draft})
        except PermissionError as error:
            self._send(403, {"error": str(error)})
        except ValueError as error:
            self._send(400, {"error": str(error)})
        except Exception as error:
            print("standalone-agreement error", repr(error))
            self._send(500, {"error": "Could not create the agreement draft."})
