import json
import os
import time
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler

import httpx


STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_SUBSCRIPTION_WEBHOOK_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def _stripe_status_to_hof(status):
    status = (status or "").lower()

    if status in ("active", "trialing", "past_due", "canceled"):
        return status

    if status in ("unpaid", "incomplete", "paused"):
        return "past_due"

    if status in ("incomplete_expired",):
        return "canceled"

    return "past_due"


def _plan_from_price(price_id):
    agent_monthly = os.environ.get("STRIPE_AGENT_MONTHLY_PRICE_ID", "")
    agent_annual = os.environ.get("STRIPE_AGENT_ANNUAL_PRICE_ID", "")
    investor_monthly = os.environ.get("STRIPE_INVESTOR_MONTHLY_PRICE_ID", "")
    investor_annual = os.environ.get("STRIPE_INVESTOR_ANNUAL_PRICE_ID", "")

    if price_id == agent_monthly:
        return "agent_starter_monthly", "agent", 10

    if price_id == agent_annual:
        return "agent_starter_annual", "agent", 10

    if price_id == investor_monthly:
        return "investor_starter_monthly", "investor", 15

    if price_id == investor_annual:
        return "investor_starter_annual", "investor", 15

    return "agent_starter", "agent", 10


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json(200, {"ok": True, "route": "stripe-webhook"})

    def do_POST(self):
        try:
            raw_body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            sig_header = self.headers.get("Stripe-Signature", "")

            if not STRIPE_WEBHOOK_SECRET:
                self._send_json(500, {"error": "Missing STRIPE_WEBHOOK_SECRET"})
                return

            if not self._verify_stripe_signature(raw_body, sig_header):
                self._send_json(400, {"error": "Invalid Stripe signature"})
                return

            event = json.loads(raw_body.decode("utf-8"))
            event_type = event.get("type", "")
            data_object = event.get("data", {}).get("object", {}) or {}

            if event_type == "checkout.session.completed":
                self._handle_checkout_completed(data_object)

            elif event_type in (
                "customer.subscription.created",
                "customer.subscription.updated",
                "customer.subscription.deleted",
            ):
                if (data_object.get("metadata") or {}).get("partner_lead_id"):
                    self._sync_partner_subscription(data_object, event_type)
                else:
                    self._handle_subscription_event(data_object, event_type)

            elif event_type == "invoice.payment_failed":
                self._handle_invoice_status(data_object, "past_due")

            # Stripe can deliver either event name for a successful invoice,
            # depending on the endpoint's configured event selection. Both are
            # safe to process: the subscription update is idempotent.
            elif event_type in ("invoice.payment_succeeded", "invoice.paid"):
                self._handle_invoice_status(data_object, "active")

            self._send_json(200, {"received": True, "event_type": event_type})

        except Exception as e:
            print("Stripe webhook error:", str(e))
            self._send_json(500, {"error": str(e)})

    def _verify_stripe_signature(self, raw_body, sig_header):
        try:
            parts = {}
            for item in sig_header.split(","):
                if "=" in item:
                    k, v = item.split("=", 1)
                    parts.setdefault(k, []).append(v)

            timestamps = parts.get("t", [])
            signatures = parts.get("v1", [])

            if not timestamps or not signatures:
                return False

            timestamp = timestamps[0]

            try:
                ts_int = int(timestamp)
                if abs(time.time() - ts_int) > 300:
                    return False
            except Exception:
                return False

            signed_payload = timestamp.encode("utf-8") + b"." + raw_body

            expected_sig = hmac.new(
                STRIPE_WEBHOOK_SECRET.encode("utf-8"),
                signed_payload,
                hashlib.sha256,
            ).hexdigest()

            return any(hmac.compare_digest(expected_sig, sig) for sig in signatures)

        except Exception:
            return False

    def _stripe_get_subscription(self, subscription_id):
        if not subscription_id:
            return None

        url = f"https://api.stripe.com/v1/subscriptions/{subscription_id}"

        with httpx.Client(timeout=15) as client:
            response = client.get(
                url,
                auth=(STRIPE_SECRET_KEY, ""),
            )
            response.raise_for_status()
            return response.json()

    def _extract_subscription_payload(self, sub, fallback_metadata=None):
        fallback_metadata = fallback_metadata or {}

        sub_id = sub.get("id", "")
        customer_id = sub.get("customer", "")
        status = _stripe_status_to_hof(sub.get("status"))

        items = sub.get("items", {}).get("data", []) or []
        first_item = items[0] if items else {}
        price = first_item.get("price", {}) or {}
        price_id = price.get("id", "")

        plan, role, packet_limit = _plan_from_price(price_id)

        metadata = {}
        metadata.update(fallback_metadata or {})
        metadata.update(sub.get("metadata", {}) or {})

        user_id = metadata.get("user_id") or metadata.get("userId") or ""
        email = metadata.get("email") or ""
        role = metadata.get("role") or role
        plan = metadata.get("plan_full") or metadata.get("plan") or plan
        brokerage_id = metadata.get("brokerage_id") or ""
        launch_source = metadata.get("launch_source") or ""

        # Stripe API versions can expose the current billing period either
        # on the subscription or on the first subscription item.
        current_period_start = sub.get("current_period_start")
        current_period_end = sub.get("current_period_end")

        if not current_period_start and first_item:
            current_period_start = first_item.get("current_period_start")

        if not current_period_end and first_item:
            current_period_end = first_item.get("current_period_end")

        cancel_at = sub.get("cancel_at")
        cancel_at_period_end = bool(sub.get("cancel_at_period_end", False))

        if cancel_at and status in ("active", "trialing"):
            cancel_at_period_end = True

        payload = {
            "role": role,
            "plan": plan,
            "status": status,
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": sub_id,
            "stripe_price_id": price_id,
            "packet_limit": packet_limit,
            "cancel_at_period_end": cancel_at_period_end,
            "updated_at": self._iso_now(),
        }

        if user_id:
            payload["user_id"] = user_id

        if current_period_start:
            payload["current_period_start"] = self._timestamp_to_iso(current_period_start)

        if current_period_end:
            payload["current_period_end"] = self._timestamp_to_iso(current_period_end)

        if cancel_at:
            payload["cancel_at"] = self._timestamp_to_iso(cancel_at)
        else:
            payload["cancel_at"] = None

        trial_start = sub.get("trial_start")
        trial_end = sub.get("trial_end")
        if trial_start:
            payload["trial_started_at"] = self._timestamp_to_iso(trial_start)
        if trial_end:
            payload["trial_ends_at"] = self._timestamp_to_iso(trial_end)
        if brokerage_id:
            payload["brokerage_id"] = brokerage_id
        if launch_source:
            payload["launch_source"] = launch_source

        return payload, user_id, email, brokerage_id

    def _handle_checkout_completed(self, session):
        metadata = session.get("metadata", {}) or {}
        partner_lead_id = metadata.get("partner_lead_id") or session.get("client_reference_id") or ""
        if partner_lead_id:
            self._mark_partner_lead_paid(partner_lead_id, session)
            return

        subscription_id = session.get("subscription", "")
        customer_id = session.get("customer", "")

        sub = self._stripe_get_subscription(subscription_id)

        if not sub:
            return

        # Carry checkout metadata onto subscription extraction.
        sub.setdefault("metadata", {})
        merged_metadata = {}
        merged_metadata.update(metadata)
        merged_metadata.update(sub.get("metadata", {}) or {})
        sub["metadata"] = merged_metadata

        payload, user_id, email, brokerage_id = self._extract_subscription_payload(sub, metadata)

        if customer_id:
            payload["stripe_customer_id"] = customer_id

        if user_id:
            self._upsert_subscription_by_user_id(payload)
            if brokerage_id:
                self._activate_brokerage_membership(user_id, email, brokerage_id)
        elif subscription_id:
            self._patch_subscription_by_stripe_subscription_id(subscription_id, payload)

    def _handle_subscription_event(self, sub, event_type):
        payload, user_id, email, brokerage_id = self._extract_subscription_payload(sub)

        if event_type == "customer.subscription.deleted":
            payload["status"] = "canceled"

        if user_id:
            self._upsert_subscription_by_user_id(payload)
            if brokerage_id and payload.get("status") in ("active", "trialing"):
                self._activate_brokerage_membership(user_id, email, brokerage_id)
        elif payload.get("stripe_subscription_id"):
            self._patch_subscription_by_stripe_subscription_id(
                payload["stripe_subscription_id"],
                payload,
            )

    def _activate_brokerage_membership(self, user_id, email, brokerage_id):
        self._require_supabase()
        self._associate_brokerage_profile(user_id, email, brokerage_id)
        members_url = (
            f"{SUPABASE_URL}/rest/v1/hof_brokerage_members"
            f"?select=id,role"
            f"&brokerage_id=eq.{brokerage_id}"
            f"&user_id=eq.{user_id}"
            "&limit=1"
        )
        headers = self._supabase_headers()
        with httpx.Client(timeout=15) as client:
            current = client.get(members_url, headers=headers)
            if current.status_code >= 300:
                raise Exception(
                    f"Brokerage membership lookup failed: "
                    f"{current.status_code} {current.text}"
                )

            existing = current.json()
            if existing:
                response = client.patch(
                    (
                        f"{SUPABASE_URL}/rest/v1/hof_brokerage_members"
                        f"?id=eq.{existing[0]['id']}"
                    ),
                    headers={**headers, "Prefer": "return=minimal"},
                    json={
                        "email": email or None,
                        "status": "active",
                        "updated_at": self._iso_now(),
                    },
                )
            else:
                response = client.post(
                    f"{SUPABASE_URL}/rest/v1/hof_brokerage_members",
                    headers={**headers, "Prefer": "return=minimal"},
                    json={
                        "brokerage_id": brokerage_id,
                        "user_id": user_id,
                        "email": email or None,
                        "role": "agent",
                        "status": "active",
                        "updated_at": self._iso_now(),
                    },
                )
            if response.status_code >= 300:
                raise Exception(
                    f"Brokerage membership activation failed: "
                    f"{response.status_code} {response.text}"
                )

    def _associate_brokerage_profile(self, user_id, email, brokerage_id):
        """Associate a paid/trialing launch enrollee without changing elevated roles.

        This runs only from the signature-verified Stripe webhook. Checkout may
        be canceled, so it must never create a brokerage relationship by itself.
        Existing broker-admin/owner profile roles are intentionally preserved.
        """
        profiles_url = f"{SUPABASE_URL}/rest/v1/hof_profiles"
        headers = self._supabase_headers()
        now = self._iso_now()

        with httpx.Client(timeout=15) as client:
            current = client.get(
                profiles_url,
                params={"id": f"eq.{user_id}", "select": "id,role,is_brokerage_admin", "limit": "1"},
                headers=headers,
            )
            if current.status_code >= 300:
                raise Exception(
                    f"Brokerage profile lookup failed: {current.status_code} {current.text}"
                )

            existing = current.json()
            if existing:
                response = client.patch(
                    f"{profiles_url}?id=eq.{user_id}",
                    headers={**headers, "Prefer": "return=minimal"},
                    json={
                        "email": email or None,
                        "brokerage_id": brokerage_id,
                        "updated_at": now,
                    },
                )
            else:
                response = client.post(
                    f"{profiles_url}?on_conflict=id",
                    headers={**headers, "Prefer": "resolution=merge-duplicates,return=minimal"},
                    json={
                        "id": user_id,
                        "email": email or None,
                        "role": "agent",
                        "brokerage_id": brokerage_id,
                        "is_brokerage_admin": False,
                        "updated_at": now,
                    },
                )

            if response.status_code >= 300:
                raise Exception(
                    f"Brokerage profile association failed: {response.status_code} {response.text}"
                )

    def _handle_invoice_status(self, invoice, status):
        subscription_id = invoice.get("subscription", "")
        if not subscription_id:
            return

        # An initial $0 trial invoice can be paid while the subscription itself
        # is still `trialing`. Do not let an invoice event accidentally turn a
        # trial into an active subscription just because Stripe delivered events
        # out of order. Stripe's current subscription object is authoritative.
        try:
            subscription = self._stripe_get_subscription(subscription_id)
        except Exception as error:
            print("Stripe subscription refresh for invoice event failed:", str(error))
            subscription = None

        if subscription:
            payload, _, _, _ = self._extract_subscription_payload(subscription)
            # A failed collection attempt must immediately remove packet access,
            # even if the subscription object has not yet reflected `past_due`.
            if status == "past_due":
                payload["status"] = "past_due"
            payload["updated_at"] = self._iso_now()
        else:
            # Preserve the existing behavior as a safe fallback so Stripe can
            # retry the webhook without losing the billing state update.
            payload = {
                "status": status,
                "updated_at": self._iso_now(),
            }

        self._patch_subscription_by_stripe_subscription_id(subscription_id, payload)

    def _upsert_subscription_by_user_id(self, payload):
        self._require_supabase()

        url = f"{SUPABASE_URL}/rest/v1/hof_subscriptions?on_conflict=user_id"

        headers = self._supabase_headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"

        with httpx.Client(timeout=15) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code >= 300:
                raise Exception(f"Supabase upsert failed: {response.status_code} {response.text}")

    def _patch_subscription_by_stripe_subscription_id(self, subscription_id, payload):
        self._require_supabase()

        url = f"{SUPABASE_URL}/rest/v1/hof_subscriptions?stripe_subscription_id=eq.{subscription_id}"

        headers = self._supabase_headers()
        headers["Prefer"] = "return=minimal"

        with httpx.Client(timeout=15) as client:
            response = client.patch(url, headers=headers, json=payload)
            if response.status_code >= 300:
                raise Exception(f"Supabase patch failed: {response.status_code} {response.text}")

    def _mark_partner_lead_paid(self, lead_id, session):
        """Move a paid founding-partner application into admin onboarding.

        Stripe is the source of truth for payment. The existing lead status remains
        intact so the admin review and placement-approval workflow is preserved.
        """
        self._require_supabase()
        payload = {
            "payment_status": "paid",
            "onboarding_status": "ready",
            "stripe_checkout_session_id": session.get("id") or None,
            "stripe_payment_intent_id": session.get("payment_intent") or None,
            "stripe_customer_id": session.get("customer") or None,
            "stripe_subscription_id": session.get("subscription") or None,
            "subscription_status": "trialing" if session.get("subscription") else None,
            "paid_at": self._iso_now(),
            "updated_at": self._iso_now(),
        }
        url = f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{lead_id}"
        headers = self._supabase_headers()
        headers["Prefer"] = "return=minimal"
        with httpx.Client(timeout=15) as client:
            response = client.patch(url, headers=headers, json=payload)
            if response.status_code >= 300:
                raise Exception(f"Partner lead payment update failed: {response.status_code} {response.text}")

    def _sync_partner_subscription(self, subscription, event_type):
        metadata = subscription.get("metadata", {}) or {}
        lead_id = metadata.get("partner_lead_id")
        if not lead_id:
            return
        status = _stripe_status_to_hof(subscription.get("status"))
        if event_type == "customer.subscription.deleted":
            status = "canceled"
        payload = {
            "stripe_subscription_id": subscription.get("id") or None,
            "stripe_customer_id": subscription.get("customer") or None,
            "subscription_status": status,
            "updated_at": self._iso_now(),
        }
        current_period_end = subscription.get("current_period_end")
        if current_period_end:
            payload["current_period_end"] = self._timestamp_to_iso(current_period_end)
        self._require_supabase()
        url = f"{SUPABASE_URL}/rest/v1/hof_partner_leads?id=eq.{lead_id}"
        headers = self._supabase_headers()
        headers["Prefer"] = "return=minimal"
        with httpx.Client(timeout=15) as client:
            response = client.patch(url, headers=headers, json=payload)
            if response.status_code >= 300:
                raise Exception(f"Partner subscription update failed: {response.status_code} {response.text}")

    def _supabase_headers(self):
        return {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

    def _require_supabase(self):
        if not SUPABASE_URL:
            raise Exception("Missing SUPABASE_URL")

        if not SUPABASE_SERVICE_ROLE_KEY:
            raise Exception("Missing SUPABASE_SERVICE_ROLE_KEY")

    def _timestamp_to_iso(self, ts):
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(ts)))
        except Exception:
            return None

    def _iso_now(self):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
