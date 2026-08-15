import os
import json
import hashlib
import hmac
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
SIGNWELL_API_KEY = os.environ.get("SIGNWELL_API_KEY", "")
# SignWell signs webhook events using the webhook ID as the HMAC key.  This is
# distinct from the API key and must never be inferred from an untrusted body.
SIGNWELL_WEBHOOK_ID = os.environ.get("SIGNWELL_WEBHOOK_ID", "").strip()
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
        _deep_get(payload, "event", "type"),
        payload.get("event_type"),
        payload.get("event"),
        payload.get("type"),
        payload.get("name"),
        _deep_get(payload, "data", "event_type"),
        _deep_get(payload, "data", "event"),
    ) or "signwell_event"


def _is_verified_event(payload):
    """Verify SignWell's event hash before any lifecycle state is changed.

    SignWell documents the signature as HMAC-SHA256 of
    ``event.type + '@' + event.time``, keyed with the webhook ID.  A missing
    configuration deliberately fails closed: the endpoint can acknowledge the
    delivery without recording telemetry or updating an offer/agreement.
    """
    if not SIGNWELL_WEBHOOK_ID or not isinstance(payload, dict):
        return False
    event = payload.get("event")
    if not isinstance(event, dict):
        return False
    event_type = event.get("type")
    event_time = event.get("time")
    supplied_hash = event.get("hash")
    if not isinstance(event_type, str) or event_time is None or not isinstance(supplied_hash, str):
        return False
    signed_value = f"{event_type}@{event_time}".encode("utf-8")
    calculated_hash = hmac.new(
        SIGNWELL_WEBHOOK_ID.encode("utf-8"), signed_value, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(supplied_hash, calculated_hash)


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
        _deep_get(payload, "data", "object", "id"),
        _deep_get(payload, "data", "object", "document_id"),
        _deep_get(payload, "data", "document", "id"),
    )


def _recipient_stats(payload):
    recipients = _first(
        payload.get("recipients"),
        _deep_get(payload, "data", "recipients"),
        _deep_get(payload, "document", "recipients"),
        _deep_get(payload, "data", "document", "recipients"),
        _deep_get(payload, "data", "object", "recipients"),
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


def _telemetry_metadata(payload, event_type, mapped_status, mapped_signwell_status):
    """Return aggregate-only webhook telemetry.

    SignWell event bodies can include signer names, email addresses, and
    document details. Those belong in SignWell's controlled audit trail, not
    in HomeOfferFlow's general operational-event table. Keep only the minimum
    lifecycle facts needed to monitor the integration.
    """
    recipient_count, signed_recipient_count, viewed_recipient_count = _recipient_stats(payload)
    return {
        "source": "signwell-webhook",
        "event_type": str(event_type or "signwell_event")[:120],
        "status": mapped_status,
        "signwell_status": mapped_signwell_status,
        "recipient_count": recipient_count,
        "signed_recipient_count": signed_recipient_count,
        "viewed_recipient_count": viewed_recipient_count,
        "payload_parse_error": payload.get("_parse_error") is True if isinstance(payload, dict) else True,
    }


async def _insert_event(document_id, event_type, payload, mapped_status, mapped_signwell_status):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    event_payload = {
        "offer_id": None,
        "user_id": None,
        "event_type": event_type,
        "status": mapped_status,
        "message": "SignWell webhook lifecycle event recorded.",
        "metadata": _telemetry_metadata(payload, event_type, mapped_status, mapped_signwell_status),
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


def _standalone_status_for(mapped_status):
    """Map the offer-oriented lifecycle label to standalone-agreement states."""
    if mapped_status == "Buyer Signed":
        return "signed"
    if mapped_status == "Rejected":
        return "void"
    # Viewed, partially signed, sent, and pending all remain executable/sent
    # from the agreement owner's perspective until SignWell reports completion.
    return "sent"


async def _update_standalone_agreement(document_id, mapped_status, mapped_signwell_status, payload):
    """Keep standalone agreement lifecycle state in sync with SignWell.

    This is intentionally a separate update from hof_offers: standalone TXR
    agreements must never be mistaken for purchase offers or appear in offer
    reporting. The query is scoped by SignWell document id, which is unique in
    the standalone table.
    """
    if not document_id or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    now = datetime.now(timezone.utc).isoformat()
    update_payload = {
        "status": _standalone_status_for(mapped_status),
        "signwell_status": mapped_signwell_status,
        "updated_at": now,
    }
    if mapped_status == "Buyer Signed":
        update_payload["signed_at"] = now
    async with httpx.AsyncClient(timeout=12) as client:
        return await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_standalone_agreements?"
            f"signwell_document_id=eq.{document_id}&select=id,status,signwell_status",
            headers=_headers(),
            json=update_payload,
        )


async def _partner_agreement_completed_in_signwell(document_id):
    """Confirm completion at SignWell before a commercial placement can unlock.

    Webhook events are useful delivery signals but must not be enough to mark a
    paid placement contract as signed. The provider API is the authoritative
    confirmation and its full response (which can include signer PII) is never
    persisted in HomeOfferFlow telemetry.
    """
    if not document_id or not SIGNWELL_API_KEY:
        return False
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"https://www.signwell.com/api/v1/documents/{document_id}",
            headers={"X-Api-Key": SIGNWELL_API_KEY},
        )
    if response.status_code != 200:
        return False
    try:
        document = response.json()
    except Exception:
        return False
    status = str(document.get("status") or document.get("document_status") or "").lower()
    return "complete" in status or "fully signed" in status


async def _update_partner_agreement(document_id, event_type):
    """Persist only verified lifecycle state for a partner commercial agreement."""
    if not document_id or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    event = str(event_type or "").lower().replace("-", "_").replace(" ", "_")
    status = None
    if "completed" in event:
        if not await _partner_agreement_completed_in_signwell(document_id):
            return None
        status = "signed"
    elif any(token in event for token in ("declined", "canceled", "cancelled")):
        status = "declined"
    elif "expired" in event:
        status = "expired"
    if not status:
        return None
    now = datetime.now(timezone.utc).isoformat()
    update_payload = {"partner_agreement_status": status, "updated_at": now}
    if status == "signed":
        update_payload["partner_agreement_signed_at"] = now
    async with httpx.AsyncClient(timeout=12) as client:
        return await client.patch(
            f"{SUPABASE_URL}/rest/v1/hof_partner_leads?"
            f"partner_agreement_signwell_document_id=eq.{document_id}"
            "&select=id,partner_agreement_status",
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
                # Do not persist undecodable provider input: it may contain
                # signer PII and is not needed to keep the endpoint healthy.
                payload = {"_parse_error": True}

            if not _is_verified_event(payload):
                # Acknowledge invalid or unconfigured deliveries so a sender
                # cannot amplify retries, but never let them affect workflow
                # state or operational metrics.
                _json(self, 200, {"status": "ignored", "reason": "invalid_webhook_signature"})
                return

            event_type = _event_type(payload)
            document_id = _document_id(payload)
            mapped_status, mapped_signwell_status = _status_for(payload)

            import asyncio
            event_resp = None
            patch_resp = None
            standalone_patch_resp = None
            partner_agreement_patch_resp = None
            try:
                event_resp = asyncio.run(_insert_event(document_id, event_type, payload, mapped_status, mapped_signwell_status))
            except Exception as e:
                print("signwell event insert failed", repr(e))
            try:
                patch_resp = asyncio.run(_update_offer(document_id, mapped_status, mapped_signwell_status, payload))
            except Exception as e:
                print("signwell offer patch failed", repr(e))
            try:
                standalone_patch_resp = asyncio.run(
                    _update_standalone_agreement(
                        document_id, mapped_status, mapped_signwell_status, payload
                    )
                )
            except Exception as e:
                print("signwell standalone agreement patch failed", repr(e))
            try:
                partner_agreement_patch_resp = asyncio.run(
                    _update_partner_agreement(document_id, event_type)
                )
            except Exception as e:
                print("signwell partner agreement patch failed", repr(e))

            _json(self, 200, {
                "status": "ok",
                "route": "signwell-webhook",
                "event_type": event_type,
                "document_id": document_id,
                "mapped_status": mapped_status,
                "mapped_signwell_status": mapped_signwell_status,
                "event_status_code": getattr(event_resp, "status_code", None),
                "patch_status_code": getattr(patch_resp, "status_code", None),
                "standalone_patch_status_code": getattr(standalone_patch_resp, "status_code", None),
                "partner_agreement_patch_status_code": getattr(partner_agreement_patch_resp, "status_code", None),
            })
        except Exception as e:
            print("signwell webhook fatal but acknowledged", repr(e))
            _json(self, 200, {"status": "acknowledged", "error_logged": str(e)})
