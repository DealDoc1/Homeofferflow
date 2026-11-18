"""Validation for signed-in agent seller-lead creation."""
from datetime import date
from decimal import Decimal, InvalidOperation
import re


FIELDS = {
    "sellerType", "propertyAddress", "sellerName", "sellerEmail", "sellerPhone",
    "askingPrice", "mortgageBalance", "desiredCloseDate", "notes",
}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _optional_text(value, label, maximum, minimum=1):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Enter valid {label}.")
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) < minimum or len(cleaned) > maximum:
        raise ValueError(f"Keep {label} between {minimum} and {maximum} characters.")
    return cleaned


def _amount(value, label):
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"Enter a valid {label}.")
    try:
        amount = Decimal(str(value).replace(",", "").replace("$", "").strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"Enter a valid {label}.")
    if not amount.is_finite() or amount < 0 or amount > Decimal("999999999999.99"):
        raise ValueError(f"Enter a non-negative {label}.")
    if amount.as_tuple().exponent < -2:
        raise ValueError(f"Enter {label} using no more than two decimal places.")
    return format(amount.quantize(Decimal("0.01")), "f")


def validate_seller_lead_creation(data):
    if not isinstance(data, dict) or set(data) != {"action", *FIELDS} or data.get("action") != "create_seller_lead":
        raise ValueError("Provide only the seller and property details.")

    seller_type = data.get("sellerType")
    if seller_type not in ("agent_listing", "fsbo"):
        raise ValueError("Choose a valid seller lead type.")
    address = _optional_text(data.get("propertyAddress"), "property address", 500, 3)
    if address is None:
        raise ValueError("Enter the property address before saving the seller lead.")

    name = _optional_text(data.get("sellerName"), "seller or landlord name", 250)
    email = _optional_text(data.get("sellerEmail"), "seller email address", 254, 3)
    if email and not EMAIL_RE.fullmatch(email):
        raise ValueError("Enter a valid seller email address or leave the optional field blank.")
    phone = _optional_text(data.get("sellerPhone"), "seller phone number", 80, 3)
    notes = _optional_text(data.get("notes"), "seller lead notes", 1500)

    close_date = data.get("desiredCloseDate")
    if close_date in (None, ""):
        close_date = None
    elif not isinstance(close_date, str):
        raise ValueError("Enter a valid target date.")
    else:
        cleaned_date = close_date.strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cleaned_date):
            raise ValueError("Enter a valid target date.")
        try:
            close_date = date.fromisoformat(cleaned_date).isoformat()
        except ValueError:
            raise ValueError("Enter a valid target date.")

    return {
        "seller_type": seller_type,
        "property_address": address,
        "seller_name": name,
        "seller_email": email.lower() if email else None,
        "seller_phone": phone,
        "asking_price": _amount(data.get("askingPrice"), "asking price or monthly rent"),
        "mortgage_balance": _amount(data.get("mortgageBalance"), "mortgage balance"),
        "desired_close_date": close_date,
        "notes": notes,
    }
