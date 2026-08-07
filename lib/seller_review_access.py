"""Secure, expiring seller-review link helpers.

Review links are intentionally separate from authenticated agent sessions. The
raw token is returned only when an agent creates a link; only its SHA-256 hash
is stored. Links are for private review and attestation only, never signing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Iterable

TOKEN_BYTES = 32
DEFAULT_TTL_DAYS = 7
MAX_SELLER_NAME = 180


def issue_token(*, ttl_days: int = DEFAULT_TTL_DAYS, now: datetime | None = None) -> dict[str, str]:
    if ttl_days < 1 or ttl_days > 30:
        raise ValueError("Review-link expiry must be between 1 and 30 days.")
    issued_at = now or datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(days=ttl_days)
    token = secrets.token_urlsafe(TOKEN_BYTES)
    return {
        "token": token,
        "token_hash": hash_token(token),
        "expires_at": expires_at.isoformat(),
    }


def hash_token(token: object) -> str:
    value = str(token or "").strip()
    if len(value) < 32 or len(value) > 256:
        raise ValueError("The seller review token is invalid.")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token_matches(token: object, expected_hash: object) -> bool:
    try:
        actual = hash_token(token)
    except ValueError:
        return False
    return hmac.compare_digest(actual, str(expected_hash or ""))


def parse_expiry(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def is_active(*, expires_at: object, revoked_at: object = None, now: datetime | None = None) -> bool:
    if revoked_at:
        return False
    expiry = parse_expiry(expires_at)
    return bool(expiry and expiry > (now or datetime.now(timezone.utc)))


def normalize_seller_name(value: object) -> str:
    return " ".join(str(value or "").strip().split()).casefold()


def seller_name_matches(candidate: object, seller_names: Iterable[object]) -> bool:
    normalized = normalize_seller_name(candidate)
    return bool(normalized) and any(normalized == normalize_seller_name(name) for name in seller_names or [])
