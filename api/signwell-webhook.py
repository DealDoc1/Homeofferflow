import os
import json
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone
import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE")
    or os.environ.get("SUPABASE_SERVICE_KEY")
    or ""
)
SIGNWELL_WEBHOOK_SECRET = os.environ.get("SIGNWELL_WEBHOOK_SECRET", "")
MAX_BODY = 300_000


def _json(handler, code, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Signwell-Signature")
    handler.end_headers()
    handler.wfile.write(body)


def _headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _deep_get(obj, *keys):
    cur = obj
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _first(*vals):
    for v in vals:
        if v is not None and v != "":
            return v
    return None


def _event_type(payload):
    return _first(
        payload.get("event_type"),
        payload.get("event"),
        payload.get("type"),
        payload.get("name"),
        _deep_get(payload, "data", "event_type"),
        _deep_get(payload, "data", "event"),
    ) or "signwell_event"


def _document_id(payload):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    document = payload.get("document") if isinstance(payload.get("document"), dict) else {}
    return _first(
        payload.get("document_id"),
        payload.get("documentId"),
        payload.get("id") if str(payload.get("id", "")).count("-") >= 2 else None,
        data.get("document_id"),
        data.get("documentId"),
        data.get("id"),
        document.get("id"),
        document.get("document_id"),
        _deep_get(payload, "data", "document", "id"),
    )


def _recipient_stats(payload):
    recipients = _first(
        payload.get("recipients"),
        _deep_get(payload, "data", "recipients"),
        _deep_get(payload, "document", "recipients"),
        _deep_get(payload, "data", "document", "recipients"),
    ) or []
    if not isinstance(recipients, list):
        recipients = []
    total = len(recipients)
    signed = 0
    viewed = 0
    for r in recipients:
        if not isinstance(r, dict):
            continue
        raw = " ".join(str(r.get(k, "")) for k in ["status", "recipient_status", "signing_status"]).lower()
        if r.get("signed") or r.get("completed") or "signed" in raw or "complete" in raw:
            signed += 1
        if r.get("viewed") or "view" in raw:
            viewed += 1
    return total, signed, viewed


def _status_for(payload):
    ev = str(_event_type(payload)).lower().replace("-", "_").replace(" ", "_")
    total, signed, viewed = _recipient_stats(payload)

    if any(x in ev for x in ["declined", "canceled", "cancelled", "expired"]):
        return "Rejected", "Declined/Expired"
    if any(x in ev for x in ["completed", "complete", "executed", "document_signed", "all_signed"]):
        return "Buyer Signed", "Buyer Signatures Complete"
    if "signed" in ev:
        if total and signed and signed < total:
            return "Partially Buyer Signed", "Partially Signed"
        return "Buyer Signed", "Buyer Signatures Complete"
    if "view" in ev:
        return "Buyer Viewed", "Viewed"
    if any(x in ev for x in ["sent", "created", "send", "document_created"]):
        return "Sent for Signature", "Awaiting Buyer Signature"

    return "Sent for Signature", "Pending"


async def _insert_event(document_id, event_type, payload, mapped_status, mapped_signwell_status):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    event_payload = {
        "event_type": event_type,
        "signwell_document_id": document_id,
        "metadata": {
            "source": "signwell-webhook",
            "status": mapped_status,
            "signwell_status": mapped_signwell_status,
            "payload": payload,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    async with httpx.AsyncClient(timeout=12) as client:
        return await client.post(f"{SUPABASE_URL}/rest/v1/hof_offer_events", headers=_headers() | {"Prefer": "return=minimal"}, json=event_payload)


async def _update_offer(document_id, mapped_status, mapped_signwell_status, payload):
    if not document_id or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    update_payload = {
        "status": mapped_status,
        "signwell_status": mapped_signwell_status,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    if mapped_status == "Buyer Signed":
        update_payload["signed_at"] = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=12) as client:
        return await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_offers?signwell_document_id=eq.{document_id}&select=id,status,signwell_status",
            headers=_headers(),
            json=update_payload,
        )


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json(self, 200, {"status": "ok"})

    def do_GET(self):
        _json(self, 200, {"status": "ok", "route": "signwell-webhook"})

    def do_POST(self):
        # Always return 200 to SignWell after logging attempt, so the webhook is not disabled for non-critical mapping errors.
        try:
            length = int(self.headers.get("content-length", "0") or "0")
            if length > MAX_BODY:
                self.rfile.read(length)
                _json(self, 200, {"status": "ignored", "reason": "body_too_large"})
                return
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                payload = {"raw": raw.decode("utf-8", errors="replace")}

            event_type = _event_type(payload)
            document_id = _document_id(payload)
            mapped_status, mapped_signwell_status = _status_for(payload)

            import asyncio
            event_resp = None
            patch_resp = None
            try:
                event_resp = asyncio.run(_insert_event(document_id, event_type, payload, mapped_status, mapped_signwell_status))
            except Exception as e:
                print("signwell event insert failed", repr(e))
            try:
                patch_resp = asyncio.run(_update_offer(document_id, mapped_status, mapped_signwell_status, payload))
            except Exception as e:
                print("signwell offer patch failed", repr(e))

            _json(self, 200, {
                "status": "ok",
                "route": "signwell-webhook",
                "event_type": event_type,
                "document_id": document_id,
                "mapped_status": mapped_status,
                "mapped_signwell_status": mapped_signwell_status,
                "event_status_code": getattr(event_resp, "status_code", None),
                "patch_status_code": getattr(patch_resp, "status_code", None),
            })
        except Exception as e:
            print("signwell webhook fatal but acknowledged", repr(e))
            _json(self, 200, {"status": "acknowledged", "error_logged": str(e)})
