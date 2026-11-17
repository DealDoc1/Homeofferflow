"""Validation rules for private seller-side offer comparison notes."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import uuid


STATUSES = {"received", "reviewing", "preferred", "declined"}
OFFER_FIELDS = {
    "offerLabel", "offerPrice", "financingType", "sellerConcessions",
    "closingDate", "optionDays", "contingencyNotes", "status", "privateNotes",
}


def normalized_uuid(value, message):
    try:
        return str(uuid.UUID(str(value or "")))
    except (TypeError, ValueError, AttributeError):
        raise ValueError(message)


def _text(value, field, max_length, *, required=False):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValueError(f"Enter valid {field}.")
    value = value.strip()
    if required and not value:
        raise ValueError(f"Enter {field}.")
    if len(value) > max_length:
        raise ValueError(f"Keep {field} to {max_length} characters or fewer.")
    return value or None


def _money(value, field):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"Enter a valid {field} amount.")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Enter a valid {field} amount.")
    if not amount.is_finite() or amount < 0 or amount > Decimal("999999999999.99"):
        raise ValueError(f"Enter a valid {field} amount.")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError(f"Enter {field} to the nearest cent.")
    return format(amount, ".2f")


def validate_offer_fields(data):
    if not isinstance(data, dict) or set(data) != OFFER_FIELDS:
        raise ValueError("Provide only the offer comparison details.")
    label = _text(data.get("offerLabel"), "offer label", 120, required=True)
    financing = _text(data.get("financingType"), "financing type", 80)
    contingencies = _text(data.get("contingencyNotes"), "contingency notes", 2000)
    private_notes = _text(data.get("privateNotes"), "private notes", 4000)

    raw_closing_date = data.get("closingDate")
    if raw_closing_date in (None, ""):
        closing_date = None
    elif isinstance(raw_closing_date, str):
        try:
            closing_date = date.fromisoformat(raw_closing_date).isoformat()
        except ValueError:
            raise ValueError("Enter a valid closing date.")
        if closing_date != raw_closing_date:
            raise ValueError("Enter a valid closing date.")
    else:
        raise ValueError("Enter a valid closing date.")

    raw_option_days = data.get("optionDays")
    if raw_option_days in (None, ""):
        option_days = None
    elif isinstance(raw_option_days, bool):
        raise ValueError("Enter option days from 0 to 365.")
    else:
        try:
            option_days = int(raw_option_days)
        except (ValueError, TypeError, OverflowError):
            raise ValueError("Enter option days from 0 to 365.")
        if str(raw_option_days).strip() != str(option_days) or not 0 <= option_days <= 365:
            raise ValueError("Enter option days from 0 to 365.")

    status = data.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("Choose a valid offer comparison status.")
    return {
        "offer_label": label,
        "offer_price": _money(data.get("offerPrice"), "offer price"),
        "financing_type": financing,
        "seller_concessions": _money(data.get("sellerConcessions"), "seller concessions"),
        "closing_date": closing_date,
        "option_days": option_days,
        "contingency_notes": contingencies,
        "status": status,
        "private_notes": private_notes,
    }


def normalize_expected_updated_at(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 64:
        raise ValueError("Reload the offer comparison before updating its status.")
    expected = value.strip()
    try:
        stamp = datetime.fromisoformat(expected.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError
    except ValueError as exc:
        raise ValueError("Refresh the workspace before changing the offer comparison.") from exc
    return expected
