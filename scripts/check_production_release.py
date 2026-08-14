#!/usr/bin/env python3
"""Verify the canonical production runtime without creating a packet.

This is intentionally a read-only health check. It validates the aggregate
20-19 packet runtime, fail-closed unsupported paths, SignWell production mode,
and the public legal/PWA pages. It never sends a SignWell document and never
exercises Stripe or Supabase mutations.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


PUBLIC_PATHS = (
    "/",
    "/ondemand",
    "/terms.html",
    "/privacy.html",
    "/disclaimer.html",
    "/esign-consent.html",
)

REQUIRED_TRUE_FLAGS = (
    "packet_runtime_ready",
    "unsupported_paths_rejected",
    "signwell_enabled",
)


def _get(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "HomeOfferFlow-release-check/1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.headers.get("content-type", ""), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("content-type", ""), exc.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def verify(origin: str, *, expected_release: str, expected_main_form: str) -> dict:
    origin = origin.rstrip("/")
    errors: list[str] = []
    status, content_type, body = _get(f"{origin}/api/fill-pdf.py")
    health: dict = {}
    if status != 200:
        errors.append(f"API health returned HTTP {status}.")
    if "json" not in content_type.lower():
        errors.append(f"API health returned unexpected content type {content_type!r}.")
    try:
        health = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append("API health response was not valid JSON.")
    if health.get("release") != expected_release:
        errors.append(f"Expected release {expected_release!r}, got {health.get('release')!r}.")
    if health.get("trec_main_form") != expected_main_form:
        errors.append(f"Expected main form {expected_main_form!r}, got {health.get('trec_main_form')!r}.")
    for flag in REQUIRED_TRUE_FLAGS:
        if health.get(flag) is not True:
            errors.append(f"Required production flag {flag!r} is not true.")
    if health.get("signwell_test_mode") is not False:
        errors.append("SignWell must be in production mode, not test mode.")

    pages = {}
    for path in PUBLIC_PATHS:
        page_status, _, _ = _get(f"{origin}{path}")
        pages[path] = page_status
        if page_status != 200:
            errors.append(f"{path} returned HTTP {page_status}.")

    return {
        "ok": not errors,
        "origin": origin,
        "release": health.get("release"),
        "trec_main_form": health.get("trec_main_form"),
        "signwell_test_mode": health.get("signwell_test_mode"),
        "public_pages": pages,
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="https://www.homeofferflow.com")
    parser.add_argument("--expected-release", default="18B-controlled-launch")
    parser.add_argument("--expected-main-form", default="20-19 production")
    args = parser.parse_args(argv)
    try:
        result = verify(
            args.origin,
            expected_release=args.expected_release,
            expected_main_form=args.expected_main_form,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
