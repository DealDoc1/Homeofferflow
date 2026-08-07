#!/usr/bin/env python3
"""Read-only smoke test for an authenticated brokerage-admin workspace.

The command validates the privacy-limited brokerage dashboard contract. It
never creates invites, changes member status, changes branding, or reads
individual offer terms. Supply an existing Supabase access token through
``HOF_ACCESS_TOKEN`` or ``--access-token``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _get(base_url: str, token: str):
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/admin-dashboard?scope=brokerage",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw or "{}")
        except json.JSONDecodeError:
            detail = {"error": raw or str(exc)}
        return exc.code, detail


def validate(payload, expected_slug=None):
    errors = []
    if not isinstance(payload, dict):
        return ["Brokerage response must be a JSON object."]
    brokerage = payload.get("brokerage") or {}
    metrics = payload.get("metrics") or {}
    privacy = payload.get("privacy") or {}
    if expected_slug and brokerage.get("slug") != expected_slug:
        errors.append("The active brokerage slug does not match the requested brokerage.")
    for key in ("memberCount", "activeMemberCount", "agentSeatCount", "offerCount", "signedCount"):
        if not isinstance(metrics.get(key), int) or metrics[key] < 0:
            errors.append(f"Missing or invalid aggregate metric: {key}.")
    for key in ("buyerDetailsIncluded", "propertyDetailsIncluded", "offerTermsIncluded", "documentContentsIncluded"):
        if privacy.get(key) is not False:
            errors.append(f"Brokerage privacy contract violated: {key} must be false.")
    if not isinstance(payload.get("agents"), list):
        errors.append("Brokerage roster is missing.")
    if not isinstance(payload.get("sourceReadiness"), list):
        errors.append("Source-readiness metadata is missing.")
    forbidden = {"buyer", "buyerEmail", "seller", "address", "offerData", "documentContents", "storagePath", "sourceSha256"}
    def contains_forbidden_key(value):
        if isinstance(value, dict):
            if forbidden.intersection(value):
                return True
            return any(contains_forbidden_key(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_forbidden_key(child) for child in value)
        return False

    for item in payload.get("agents") or []:
        if contains_forbidden_key(item):
            errors.append("Brokerage roster contains a buyer, offer-detail, or source-secret field.")
            break
    for item in payload.get("sourceReadiness") or []:
        if contains_forbidden_key(item):
            errors.append("Source-readiness payload contains a private source field.")
            break
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://www.homeofferflow.com")
    parser.add_argument("--access-token", default=os.environ.get("HOF_ACCESS_TOKEN"))
    parser.add_argument("--brokerage-slug", default="ondemand")
    args = parser.parse_args(argv)
    if not args.access_token:
        parser.error("An existing Supabase access token is required via --access-token or HOF_ACCESS_TOKEN.")
    status, payload = _get(args.base_url, args.access_token)
    if status >= 300:
        print(json.dumps({"ok": False, "httpStatus": status, "response": payload}, indent=2), file=sys.stderr)
        return 2
    errors = validate(payload, args.brokerage_slug)
    report = {
        "ok": not errors,
        "brokerage": {"name": (payload.get("brokerage") or {}).get("name"), "slug": (payload.get("brokerage") or {}).get("slug")},
        "memberCount": (payload.get("metrics") or {}).get("memberCount"),
        "activeMemberCount": (payload.get("metrics") or {}).get("activeMemberCount"),
        "agentSeatCount": (payload.get("metrics") or {}).get("agentSeatCount"),
        "pendingInviteCount": len(payload.get("pendingInvites") or []),
        "sourceReadinessCount": len(payload.get("sourceReadiness") or []),
        "privacy": payload.get("privacy") or {},
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
