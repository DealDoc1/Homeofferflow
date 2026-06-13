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

STATUS_MAP = {
    "document_sent": "Awaiting Signature",
    "document_send": "Awaiting Signature",
    "sent": "Awaiting Signature",
    "document_viewed": "Viewed",
    "viewed": "Viewed",
    "document_completed": "Signed",
    "document_complete": "Signed",
    "completed": "Signed",
    "complete": "Signed",
    "document_declined": "Declined",
    "declined": "Declined",
    "document_expired": "Expired",
    "expired": "Expired",
}


def json_response(handler, code, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def pick_event_type(payload):
    for key in ("event", "event_type", "type", "action"):
        val = payload.get(key)
        if val:
            return str(val).strip()
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    for key in ("event", "event_type", "type", "action"):
        val = data.get(key)
        if val:
            return str(val).strip()
    return ""


def pick_document(payload):
    candidates = [
        payload.get("document"),
        payload.get("data", {}).get("document") if isinstance(payload.get("data"), dict) else None,
        payload.get("data", {}).get("object") if isinstance(payload.get("data"), dict) else None,
        payload.get("object"),
        payload,
    ]
    for c in candidates:
        if isinstance(c, dict):
            doc_id = c.get("id") or c.get("document_id") or c.get("documentId")
            if doc_id:
                return c
    return {}


def update_supabase(document_id, status, event_type, payload):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    now = datetime.now(timezone.utc).isoformat()
    update_payload = {
        "signwell_status": status,
        "status": status,
        "last_updated": now,
    }

    with httpx.Client(timeout=20) as client:
        r = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_offers",
            params={"signwell_document_id": f"eq.{document_id}", "select": "id,user_id,signwell_document_id"},
            headers=headers,
            json=update_payload,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Supabase offer update failed {r.status_code}: {r.text[:1000]}")
        rows = r.json() if r.text else []

        for row in rows:
            event_payload = {
                "offer_id": row.get("id"),
                "user_id": row.get("user_id"),
                "event_type": "signwell_webhook",
                "status": status,
                "message": f"SignWell {event_type} received.",
                "metadata": {
                    "signwell_document_id": str(document_id),
                    "signwell_event": event_type,
                    "raw": payload,
                },
                "created_at": now,
            }
            er = client.post(
                f"{SUPABASE_URL}/rest/v1/hof_offer_events",
                headers={**headers, "Prefer": "return=minimal"},
                json=event_payload,
            )
            if er.status_code >= 300:
                print("Supabase event insert failed:", er.status_code, er.text[:1000])

    return rows


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        json_response(self, 200, {"status": "ok", "route": "signwell-webhook"})

    def do_POST(self):
        try:
            if SIGNWELL_WEBHOOK_SECRET:
                provided = (
                    self.headers.get("x-signwell-webhook-secret")
                    or self.headers.get("x-webhook-secret")
                    or self.headers.get("authorization", "").replace("Bearer ", "")
                )
                if provided != SIGNWELL_WEBHOOK_SECRET:
                    json_response(self, 401, {"error": "Unauthorized webhook"})
                    return

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8") or "{}")

            event_type = pick_event_type(payload)
            doc = pick_document(payload)
            document_id = doc.get("id") or doc.get("document_id") or doc.get("documentId")
            if not document_id:
                json_response(self, 200, {"status": "ignored", "reason": "missing document id"})
                return

            normalized = event_type.lower().replace(".", "_").replace("-", "_").strip()
            status = STATUS_MAP.get(normalized)
            if not status:
                json_response(self, 200, {"status": "ignored", "event_type": event_type, "document_id": str(document_id)})
                return

            rows = update_supabase(str(document_id), status, event_type, payload)
            json_response(self, 200, {"status": "ok", "document_id": str(document_id), "new_status": status, "matched_offers": len(rows)})

        except Exception as e:
            print("SIGNWELL WEBHOOK ERROR:", str(e))
            json_response(self, 500, {"error": str(e)})
