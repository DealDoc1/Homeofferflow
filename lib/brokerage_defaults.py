"""Owner-confirmed brokerage identity defaults, never agent license numbers."""
import re


ONDEMAND_BROKER_LICENSE = "9010832"


def broker_license(name, value=None):
    existing = str(value or "").strip()
    if existing:
        return existing
    normalized = re.sub(r"[^a-z0-9]", "", str(name or "").lower())
    return ONDEMAND_BROKER_LICENSE if normalized == "ondemandrealty" else ""
