#!/usr/bin/env python3
"""Upload already-authorized private TXR PDFs through the admin source gate.

This command intentionally requires an existing Supabase access token. It does
not use a service-role key, write directly to Storage, or create source rows.
The server endpoint remains responsible for platform-admin authorization,
fingerprint verification, duplicate detection, and private storage.

Example (run locally, never commit the token):

  HOF_ACCESS_TOKEN='...' python scripts/upload_private_txr_sources.py \
    '/private/path/HomeOfferFlow' --base-url https://www.homeofferflow.com \
    --brokerage-slug ondemand --dry-run

Remove ``--dry-run`` only after reviewing the inventory and the destination.

For a local inventory without network access or a token:

  python scripts/upload_private_txr_sources.py \
    '/private/path/HomeOfferFlow' --inventory-only
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from scripts.verify_private_txr_sources import EXPECTED, verify
except ModuleNotFoundError:  # direct `python scripts/...` execution from repo root
    from verify_private_txr_sources import EXPECTED, verify


def _request(base_url: str, token: str, method: str, path: str, payload=None):
    body = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw or "{}")
        except json.JSONDecodeError:
            detail = {"error": raw or str(exc)}
        return exc.code, detail


def _select_brokerage(brokerages, brokerage_id: str | None, brokerage_slug: str | None):
    if bool(brokerage_id) == bool(brokerage_slug):
        raise ValueError("Provide exactly one of --brokerage-id or --brokerage-slug.")
    matches = [
        item for item in brokerages
        if (brokerage_id and item.get("id") == brokerage_id)
        or (brokerage_slug and item.get("slug") == brokerage_slug)
    ]
    if len(matches) != 1:
        raise ValueError("The requested brokerage was not uniquely found in the active list.")
    return matches[0]


def _payload(path: Path, form_code: str, revision: str, brokerage_id: str, attested: bool):
    content = path.read_bytes()
    return {
        "brokerageId": brokerage_id,
        "formCode": form_code,
        "sourceRevision": revision,
        "originalFilename": path.name,
        "sourceSha256": hashlib.sha256(content).hexdigest(),
        "contentBase64": base64.b64encode(content).decode("ascii"),
        "authorizationAttested": attested,
    }


def _inventory(directory: Path):
    """Return the verified local source plan without contacting the API."""
    results = verify(directory)
    if not all(item["ok"] for item in results):
        return None, results
    plan = []
    for form_code, expected in EXPECTED.items():
        path = directory / expected["filename"]
        plan.append({
            "formCode": form_code,
            "revision": expected["revision"],
            "filename": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return plan, results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Private directory containing the four TXR PDFs")
    parser.add_argument("--base-url", default="https://www.homeofferflow.com", help="HomeOfferFlow origin")
    parser.add_argument("--access-token", default=os.environ.get("HOF_ACCESS_TOKEN"), help="Supabase access token (or HOF_ACCESS_TOKEN)")
    parser.add_argument("--brokerage-id")
    parser.add_argument("--brokerage-slug")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Verify the destination and print the upload plan without sending PDFs")
    mode.add_argument("--inventory-only", action="store_true", help="Verify local PDFs and print their upload plan without a token or network request")
    args = parser.parse_args(argv)
    directory = args.directory.expanduser().resolve()
    plan, results = _inventory(directory)
    if plan is None:
        print(json.dumps({"all_ok": False, "sources": results}, indent=2), file=sys.stderr)
        return 2

    if args.inventory_only:
        print(json.dumps({"ok": True, "inventoryOnly": True, "sources": plan}, indent=2))
        return 0

    if not args.access_token:
        parser.error("An existing Supabase access token is required via --access-token or HOF_ACCESS_TOKEN.")

    status, brokerage_payload = _request(
        args.base_url, args.access_token, "GET", "/api/admin-dashboard?scope=platform_source_brokerages"
    )
    if status >= 300:
        print(json.dumps(brokerage_payload, indent=2), file=sys.stderr)
        return 3
    try:
        brokerage = _select_brokerage(
            brokerage_payload.get("brokerages", []), args.brokerage_id, args.brokerage_slug
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 4

    for item in plan:
        form_code = item["formCode"]
        expected = EXPECTED[form_code]
        path = directory / expected["filename"]
        payload = _payload(path, form_code, expected["revision"], brokerage["id"], True)
        if not args.dry_run:
            upload_status, response = _request(
                args.base_url, args.access_token, "POST", "/api/admin-dashboard", {
                    "action": "upload_platform_form_source",
                    **payload,
                }
            )
            if upload_status >= 300:
                print(json.dumps({"ok": False, "formCode": form_code, "response": response}, indent=2), file=sys.stderr)
                return 5
            print(json.dumps(response, indent=2))

    print(json.dumps({"ok": True, "dryRun": args.dry_run, "brokerage": brokerage, "sources": plan}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
