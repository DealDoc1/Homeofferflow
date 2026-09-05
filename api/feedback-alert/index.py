import json
import os
import hashlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

import httpx


RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FEEDBACK_ALERT_TO = os.environ.get("FEEDBACK_ALERT_TO") or os.environ.get("ADMIN_EMAIL") or "support@homeofferflow.com"
FROM_EMAIL = (
    os.environ.get("FEEDBACK_FROM_EMAIL")
    or os.environ.get("RESEND_TRANSACTION_FROM_EMAIL")
    or os.environ.get("FROM_EMAIL")
    or "HomeOfferFlow Offers <offers@offers.homeofferflow.com>"
)


def _safe(value, fallback=""):
    if value is None:
        return fallback
    return str(value)


def _html_escape(value):
    return (_safe(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _feedback_from_header():
    return FROM_EMAIL if "<" in FROM_EMAIL else f"HomeOfferFlow Feedback <{FROM_EMAIL}>"


def _build_email(payload):
    feedback = payload.get("feedback") or {}
    issue_type = _safe(payload.get("issueType") or feedback.get("issue_type") or "feedback")
    account_email = _safe(payload.get("accountEmail") or feedback.get("email") or "unknown")
    role = _safe(payload.get("role") or feedback.get("role") or "")
    message = _safe(payload.get("message") or feedback.get("message") or "")
    page_url = _safe(payload.get("pageUrl") or feedback.get("page_url") or "")
    user_agent = _safe(payload.get("userAgent") or feedback.get("user_agent") or "")
    feedback_id = _safe(feedback.get("id") or "")
    created_at = _safe(feedback.get("created_at") or datetime.now(timezone.utc).isoformat())

    subject = f"HomeOfferFlow product feedback: {issue_type}"

    text = f"""New HomeOfferFlow product feedback

Issue type: {issue_type}
Account: {account_email}
Role: {role}
Feedback ID: {feedback_id}
Created: {created_at}

Message:
{message}

Page URL:
{page_url}

User agent:
{user_agent}
"""

    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#111827;">
      <h2>New HomeOfferFlow product feedback</h2>
      <p><strong>Issue type:</strong> {_html_escape(issue_type)}<br>
      <strong>Account:</strong> {_html_escape(account_email)}<br>
      <strong>Role:</strong> {_html_escape(role)}<br>
      <strong>Feedback ID:</strong> {_html_escape(feedback_id)}<br>
      <strong>Created:</strong> {_html_escape(created_at)}</p>
      <h3>Message</h3>
      <div style="white-space:pre-wrap;background:#f3f4f6;border:1px solid #e5e7eb;border-radius:8px;padding:12px;">{_html_escape(message)}</div>
      <h3>Context</h3>
      <p><strong>Page URL:</strong><br>{_html_escape(page_url)}</p>
      <p><strong>User agent:</strong><br>{_html_escape(user_agent)}</p>
    </div>
    """

    return subject, text, html


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json(200, {"ok": True, "route": "feedback-alert"})

    def do_POST(self):
        try:
            raw_body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            payload = json.loads(raw_body.decode("utf-8") or "{}")

            message = _safe(payload.get("message") or (payload.get("feedback") or {}).get("message"))
            if not message.strip():
                self._send_json(400, {"error": "Missing feedback message"})
                return

            if not RESEND_API_KEY:
                self._send_json(500, {"error": "Missing RESEND_API_KEY"})
                return

            subject, text, html = _build_email(payload)

            resend_payload = {
                "from": _feedback_from_header(),
                "to": [FEEDBACK_ALERT_TO],
                "subject": subject,
                "text": text,
                "html": html,
                "tags": [{"name": "message_type", "value": "product_feedback"}],
            }
            feedback_ref = _safe((payload.get("feedback") or {}).get("id") or "")
            fingerprint = hashlib.sha256(
                f"{FEEDBACK_ALERT_TO}|{subject}|{text}".encode("utf-8")
            ).hexdigest()
            idempotency_key = f"hof/product_feedback/{feedback_ref or fingerprint}"

            with httpx.Client(timeout=15) as client:
                response = client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                        "Idempotency-Key": idempotency_key[:256],
                    },
                    json=resend_payload,
                )

            if response.status_code >= 300:
                self._send_json(response.status_code, {
                    "error": "Resend email failed",
                    "details": response.text[:500],
                })
                return

            data = response.json() if response.text else {}
            self._send_json(200, {"ok": True, "email_id": data.get("id")})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
