"""Validation and canonical serialization for an agent's private contract timeline."""
from datetime import date, datetime, timezone
import re


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TRACKING_VERSION = 2


def _date(value, label, *, required=False):
    if value in (None, "") and not required:
        return ""
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ValueError(f"Enter a valid {label} date.")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Enter a valid {label} date.")
    return value


def normalize_milestones(rows, *, reject_duplicates=False):
    if rows is None:
        return []
    if not isinstance(rows, list) or len(rows) > 12:
        raise ValueError("Add no more than 12 confirmed dates.")
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"label", "date"}:
            raise ValueError("Each confirmed date needs only a name and date.")
        label = str(row.get("label") or "").strip()
        value = str(row.get("date") or "").strip()
        if not label and not value:
            continue
        if not 2 <= len(label) <= 80:
            raise ValueError("For each added date, enter a short name and the date shown in the signed contract or a written amendment.")
        duplicate_key = (" ".join(label.split()).lower(), value)
        if reject_duplicates and duplicate_key in seen:
            raise ValueError("Enter each confirmed date once. If an amendment changed it, use a distinct name for the updated date.")
        seen.add(duplicate_key)
        result.append({"label": label, "date": _date(value, "confirmed")})
    return result


def build_tracking(data, option_days, *, now=None):
    """Validate client inputs and derive only the already-disclosed option date."""
    if not isinstance(data, dict):
        raise ValueError("Provide the confirmed contract dates.")
    effective = _date(data.get("effectiveDate"), "effective", required=True)
    closing = _date(data.get("closingDate"), "closing")
    days = 0
    if type(option_days) is int and 0 < option_days <= 365:
        days = option_days
    option_date = ""
    if days:
        from datetime import timedelta
        try:
            option_date = (date.fromisoformat(effective) + timedelta(days=days)).isoformat()
        except OverflowError:
            raise ValueError("Enter an effective date that can support the saved option period.")
    timestamp = now or datetime.now(timezone.utc)
    return {
        "version": TRACKING_VERSION,
        "acceptedContractConfirmed": True,
        "effectiveDate": effective,
        "optionDeadline": option_date,
        "closingDate": closing,
        "milestones": normalize_milestones(data.get("milestones"), reject_duplicates=True),
        "updatedAt": timestamp.astimezone(timezone.utc).isoformat(),
    }


def project_tracking(value):
    """Return only validated timeline fields needed to reopen an agent timeline."""
    if not isinstance(value, dict):
        return {}
    projected = {}
    if type(value.get("version")) is int and value["version"] > 0:
        projected["version"] = value["version"]
    if isinstance(value.get("acceptedContractConfirmed"), bool):
        projected["acceptedContractConfirmed"] = value["acceptedContractConfirmed"]
    for key, label in (
        ("effectiveDate", "effective"),
        ("optionDeadline", "option-period"),
        ("closingDate", "closing"),
    ):
        if isinstance(value.get(key), str):
            try:
                projected[key] = _date(value[key], label)
            except ValueError:
                continue
    updated_at = value.get("updatedAt")
    if isinstance(updated_at, str) and 0 < len(updated_at) <= 64:
        try:
            parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            pass
        else:
            if parsed.tzinfo is not None:
                projected["updatedAt"] = updated_at
    if isinstance(value.get("milestones"), list):
        try:
            projected["milestones"] = normalize_milestones(value["milestones"])
        except ValueError:
            pass
    return projected
