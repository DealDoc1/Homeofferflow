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
    "document_sent": "Awaiting Buyer Signature",
    "document_send": "Awaiting Buyer Signature",
    "document_created": "Awaiting Buyer Signature",
    "document_create": "Awaiting Buyer Signature",
    "created": "Awaiting Buyer Signature",
    "sent": "Awaiting Buyer Signature",

    "document_viewed": "Viewed",
    "document_view": "Viewed",
    "viewed": "Viewed",
    "view": "Viewed",

    "document_in_progress": "Partially Signed",
    "in_progress": "Partially Signed",
    "inprogress": "Partially Signed",
    "partially_signed": "Partially Signed",
    "partial_signed": "Partially Signed",

    "document_completed": "Buyer Signatures Complete",
    "document_complete": "Buyer Signatures Complete",
    "completed": "Buyer Signatures Complete",
    "complete": "Buyer Signatures Complete",
    "signed": "Buyer Signatures Complete",

    "document_declined": "Declined",
    "declined": "Declined",

    "document_expired": "Expired",
    "expired": "Expired",
}


def json_response(handler, code, payload):
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def normalize_event_type(value):
    return str(value or "").lower().replace(".", "_").replace("-", "_").replace(" ", "_").strip()


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

    document = payload.get("document") if isinstance(payload.get("document"), dict) else {}
    for key in ("event", "event_type", "type", "action", "status"):
        val = document.get(key)
        if val:
            return str(val).strip()

    return ""


def pick_document(payload):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    candidates = [
        payload.get("document"),
        data.get("document") if isinstance(data, dict) else None,
        data.get("object") if isinstance(data, dict) else None,
        payload.get("object"),
        payload,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            doc_id = (
                candidate.get("id")
                or candidate.get("document_id")
                or candidate.get("documentId")
                or candidate.get("document")
            )
            if doc_id:
                return candidate

    return {}


def pick_document_id(payload):
    doc = pick_document(payload)

    candidates = [
        doc.get("id"),
        doc.get("document_id"),
        doc.get("documentId"),
        doc.get("document"),
        payload.get("document_id"),
        payload.get("documentId"),
        payload.get("document"),
    ]

    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    candidates.extend([
        data.get("id"),
        data.get("document_id"),
        data.get("documentId"),
        data.get("document"),
    ])

    for value in candidates:
        if value:
            return str(value)

    return ""


def pick_status(payload, event_type):
    normalized = normalize_event_type(event_type)
    if normalized in STATUS_MAP:
        return STATUS_MAP[normalized]

    doc = pick_document(payload)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    raw_status = (
        doc.get("status")
        or doc.get("document_status")
        or data.get("status")
        or data.get("document_status")
        or payload.get("status")
        or payload.get("document_status")
        or ""
    )

    normalized_status = normalize_event_type(raw_status)
    return STATUS_MAP.get(normalized_status, "")


def supabase_headers(prefer="return=representation"):
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }


def update_supabase(document_id, status, event_type, payload):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    now = datetime.now(timezone.utc).isoformat()

    update_payload = {
        "signwell_status": status,
        "status": status,
        "last_updated": now,
    }

    with httpx.Client(timeout=20) as client:
        update_response = client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_offers",
            params={
                "signwell_document_id": f"eq.{document_id}",
                "select": "id,user_id,signwell_document_id,status,signwell_status",
            },
            headers=supabase_headers("return=representation"),
            json=update_payload,
        )

        if update_response.status_code >= 300:
            raise RuntimeError(
                f"Supabase offer update failed {update_response.status_code}: {update_response.text[:1000]}"
            )

        rows = update_response.json() if update_response.text else []

        if rows:
            for row in rows:
                event_payload = {
                    "offer_id": row.get("id"),
                    "user_id": row.get("user_id"),
                    "event_type": "signwell_webhook",
                    "status": status,
                    "message": f"SignWell {event_type} received.",
                    "metadata": {
                        "matched": True,
                        "signwell_document_id": str(document_id),
                        "signwell_event": event_type,
                        "raw": payload,
                    },
                    "created_at": now,
                }

                event_response = client.post(
                    f"{SUPABASE_URL}/rest/v1/hof_offer_events",
                    headers=supabase_headers("return=minimal"),
                    json=event_payload,
                )

                if event_response.status_code >= 300:
                    print("Supabase event insert failed:", event_response.status_code, event_response.text[:1000])
        else:
            event_payload = {
                "offer_id": None,
                "user_id": None,
                "event_type": "signwell_webhook_unmatched",
                "status": status,
                "message": f"SignWell {event_type} received but no hof_offers row matched document id.",
                "metadata": {
                    "matched": False,
                    "signwell_document_id": str(document_id),
                    "signwell_event": event_type,
                    "raw": payload,
                },
                "created_at": now,
            }

            event_response = client.post(
                f"{SUPABASE_URL}/rest/v1/hof_offer_events",
                headers=supabase_headers("return=minimal"),
                json=event_payload,
            )

            if event_response.status_code >= 300:
                print("Supabase unmatched event insert failed:", event_response.status_code, event_response.text[:1000])

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
            document_id = pick_document_id(payload)

            if not document_id:
                json_response(self, 200, {
                    "status": "ignored",
                    "reason": "missing document id",
                    "event_type": event_type,
                })
                return

            status = pick_status(payload, event_type)

            if not status:
                json_response(self, 200, {
                    "status": "ignored",
                    "reason": "unmapped event/status",
                    "event_type": event_type,
                    "document_id": str(document_id),
                })
                return

            rows = update_supabase(str(document_id), status, event_type, payload)

            json_response(self, 200, {
                "status": "ok",
                "document_id": str(document_id),
                "new_status": status,
                "matched_offers": len(rows),
            })

        except Exception as e:
            print("SIGNWELL WEBHOOK ERROR:", str(e))
            json_response(self, 500, {"error": str(e)})
