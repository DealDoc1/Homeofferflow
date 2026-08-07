"""Email-verified seller review credentials.

The review URL token identifies a pending request, but it cannot reveal any
seller/property data by itself. A six-digit code sent to the seller's email
creates a short-lived review session. The session is what permits PDF preview
and attestation; signing remains deliberately unavailable.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import re
import secrets
from typing import Iterable

TOKEN_BYTES = 32
SESSION_BYTES = 32
DEFAULT_TTL_DAYS = 7
SESSION_TTL_MINUTES = 30
EMAIL_RE = re.compile(r"(?=.{3,254}$)[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: object) -> str:
    result = str(value or "").strip().lower()
    if not EMAIL_RE.fullmatch(result):
        raise ValueError("Enter a valid seller email address.")
    return result


def issue_credentials(*, ttl_days: int = DEFAULT_TTL_DAYS, now: datetime | None = None) -> dict[str, str]:
    if ttl_days < 1 or ttl_days > 30:
        raise ValueError("Review-link expiry must be between 1 and 30 days.")
    issued_at = now or datetime.now(timezone.utc)
    token = secrets.token_urlsafe(TOKEN_BYTES)
    code = f"{secrets.randbelow(1_000_000):06d}"
    token_hash = hash_secret(token)
    return {
        "token": token,
        "token_hash": token_hash,
        "code": code,
        "verification_code_hash": hash_code(code, token_hash),
        "expires_at": (issued_at + timedelta(days=ttl_days)).isoformat(),
    }


def issue_session(*, now: datetime | None = None) -> dict[str, str]:
    issued_at = now or datetime.now(timezone.utc)
    token = secrets.token_urlsafe(SESSION_BYTES)
    return {
        "token": token,
        "token_hash": hash_secret(token),
        "expires_at": (issued_at + timedelta(minutes=SESSION_TTL_MINUTES)).isoformat(),
    }


def hash_secret(value: object) -> str:
    raw = str(value or "").strip()
    if len(raw) < 32 or len(raw) > 256:
        raise ValueError("The review credential is invalid.")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_code(code: object, token_hash: str) -> str:
    value = str(code or "").strip()
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError("The review verification code is invalid.")
    return hmac.new(token_hash.encode("ascii"), value.encode("ascii"), hashlib.sha256).hexdigest()


def code_matches(code: object, token_hash: str, expected_hash: object) -> bool:
    try:
        actual = hash_code(code, token_hash)
    except ValueError:
        return False
    return hmac.compare_digest(actual, str(expected_hash or ""))


def parse_expiry(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def is_active(value: object, *, now: datetime | None = None) -> bool:
    parsed = parse_expiry(value)
    return bool(parsed and parsed > (now or datetime.now(timezone.utc)))


def normalize_seller_name(value: object) -> str:
    return " ".join(str(value or "").strip().split()).casefold()


def seller_name_matches(candidate: object, seller_names: Iterable[object]) -> bool:
    normalized = normalize_seller_name(candidate)
    return bool(normalized) and any(normalized == normalize_seller_name(name) for name in seller_names or [])
