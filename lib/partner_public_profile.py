"""Explicit public creative, never fallback to a partner's internal contacts."""
import re

PUBLIC_PROFILE_COLUMNS = (
    "onboarding_public_contact_name",
    "onboarding_public_contact_phone",
    "onboarding_public_description",
)


def public_phone(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    if not re.fullmatch(r"\+?[0-9() .-]{7,30}", raw):
        raise ValueError("Enter a valid public phone number, without an extension.")
    digits = re.sub(r"[^0-9]", "", raw)
    if not raw.startswith("+") and len(digits) == 10:
        digits = "1" + digits
    elif not raw.startswith("+") and not (len(digits) == 11 and digits.startswith("1")):
        raise ValueError("Use a ten-digit US number or include the country code with +.")
    if not re.fullmatch(r"[1-9][0-9]{9,14}", digits):
        raise ValueError("Enter a valid public phone number.")
    return "+" + digits


def public_profile_update(data, previous=None):
    previous = previous or {}
    result = {}
    for field, limit in (("public_contact_name", 80), ("public_description", 600)):
        column = "onboarding_" + field
        value = str(data.get(field, previous.get(column)) or "").strip()
        if len(value) > limit:
            raise ValueError(f"Public {'contact name' if limit == 80 else 'description'} is too long.")
        result[column] = value or None
    column = "onboarding_public_contact_phone"
    result[column] = public_phone(data.get("public_contact_phone", previous.get(column)))
    return result


def approved_public_profile(lead):
    """Return only opted-in creative. Invalid stored phone cannot become a URI."""
    try:
        phone = public_phone(lead.get("onboarding_public_contact_phone"))
    except ValueError:
        phone = None
    return {
        "partner_program": "beta" if str(lead.get("partner_program") or "").lower() == "beta" else "commercial",
        "public_contact_name": str(lead.get("onboarding_public_contact_name") or "").strip()[:80],
        "public_contact_phone": phone or "",
        "public_description": str(lead.get("onboarding_public_description") or "").strip()[:600],
    }
