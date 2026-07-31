"""Isolated SignWell signer/field map for TXR-1507.

This map is intentionally separate from offer-packet SignWell coordinates.
It only builds a payload fragment after the caller supplies an explicit signer
plan. It does not send a document or enable a signing workflow by itself.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping


class TXR1507SignerPlanError(ValueError):
    pass


def _person(value: Any, label: str) -> Dict[str, str]:
    if not isinstance(value, Mapping):
        raise TXR1507SignerPlanError(f"{label} signer details are required.")
    name = " ".join(str(value.get("name") or "").split())
    email = str(value.get("email") or "").strip().lower()
    if not name or len(name) > 180:
        raise TXR1507SignerPlanError(f"{label} signer name is required.")
    if "@" not in email or len(email) > 254:
        raise TXR1507SignerPlanError(f"{label} signer email is invalid.")
    return {"name": name, "email": email}


def normalize_txr_1507_signer_plan(plan: Mapping[str, Any]) -> Dict[str, Any]:
    """Require an explicit broker-vs-associate and one/two client plan."""
    if not isinstance(plan, Mapping):
        raise TXR1507SignerPlanError("An explicit TXR-1507 signer plan is required.")
    broker_role = str(plan.get("broker_role") or plan.get("brokerRole") or "").strip().lower()
    if broker_role not in {"broker", "associate"}:
        raise TXR1507SignerPlanError("Choose whether the broker or broker associate will sign.")
    signer_key = "broker" if broker_role == "broker" else "associate"
    primary = _person(plan.get(signer_key), "Broker" if broker_role == "broker" else "Associate")
    raw_clients = plan.get("clients")
    if not isinstance(raw_clients, list) or not 1 <= len(raw_clients) <= 2:
        raise TXR1507SignerPlanError("TXR-1507 requires one or two client signers.")
    clients = [_person(value, f"Client {index + 1}") for index, value in enumerate(raw_clients)]
    emails = [primary["email"], *(client["email"] for client in clients)]
    if len(set(emails)) != len(emails):
        raise TXR1507SignerPlanError("Every TXR-1507 signer must use a different email address.")
    return {"broker_role": broker_role, "primary": primary, "clients": clients}


def build_txr_1507_signwell_fields(signer_plan: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Build the isolated two-page field map in SignWell's 816x1056 space.

    Coordinates are based on the authorized TXR-1507 06-15-26 source. They are
    provisional until completed SignWell packets are visually inspected.
    """
    plan = normalize_txr_1507_signer_plan(signer_plan)
    fields: List[Dict[str, Any]] = []

    def add(api_id, field_type, page, x, y, recipient_id, width, height, **extra):
        fields.append({
            "api_id": api_id,
            "type": field_type,
            "page": page,
            "x": x,
            "y": y,
            "recipient_id": str(recipient_id),
            "required": True,
            "width": width,
            "height": height,
            **extra,
        })

    # Page 1 identification initials: broker/associate, then each client.
    add("txr1507_primary_initials", "initials", 1, 420, 988, 1, 28, 12)
    add("txr1507_client1_initials", "initials", 1, 572, 988, 2, 28, 12)
    if len(plan["clients"]) == 2:
        add("txr1507_client2_initials", "initials", 1, 675, 988, 3, 28, 12)

    # Page 2 printed signatures. The source offers either broker or broker
    # associate signature, so only the explicitly selected primary signer gets
    # a field. Dates are locked to SignWell's date field.
    add("txr1507_primary_signature", "signature", 2, 80, 720, 1, 180, 24)
    add("txr1507_primary_date", "date", 2, 335, 720, 1, 76, 18, date_format="MM/DD/YYYY", lock_sign_date=True)
    add("txr1507_client1_signature", "signature", 2, 440, 720, 2, 180, 24)
    add("txr1507_client1_date", "date", 2, 720, 720, 2, 76, 18, date_format="MM/DD/YYYY", lock_sign_date=True)
    if len(plan["clients"]) == 2:
        add("txr1507_client2_signature", "signature", 2, 440, 836, 3, 180, 24)
        add("txr1507_client2_date", "date", 2, 720, 836, 3, 76, 18, date_format="MM/DD/YYYY", lock_sign_date=True)
    return fields


def build_txr_1507_recipients(signer_plan: Mapping[str, Any]) -> List[Dict[str, str]]:
    plan = normalize_txr_1507_signer_plan(signer_plan)
    recipients = [{"id": "1", "name": plan["primary"]["name"], "email": plan["primary"]["email"]}]
    recipients.extend(
        {"id": str(index + 2), "name": client["name"], "email": client["email"]}
        for index, client in enumerate(plan["clients"])
    )
    return recipients
