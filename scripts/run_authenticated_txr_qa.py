#!/usr/bin/env python3
"""Create and download a private TXR-1507 preview for authenticated QA.

This helper never sends a SignWell document. It uses an existing Supabase
access token, creates a private draft through the authenticated production
API, downloads the private preview PDF, and writes a metadata-only report.
No client names, addresses, compensation values, tokens, or source URLs are
written to the report.

Usage::

    HOF_ACCESS_TOKEN='...' python scripts/run_authenticated_txr_qa.py \
      --output-dir /tmp/txr-1507-qa --clients 1

Use ``--clients 2`` for the two-client signer-plan scenario.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCE_ID = "016b54b3-61e9-4857-a048-f62f04fb8db9"
FORM_CODE = "TXR-1507"


def _request(base_url: str, token: str, path: str, *, method="GET", body=None):
    headers = {"Authorization": f"Bearer {token}"}
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}", headers=headers, method=method, data=payload
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, response.headers.get("content-type", ""), response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HomeOfferFlow API returned HTTP {exc.code}: {detail[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach HomeOfferFlow: {exc.reason}") from exc


def _payload(client_count: int):
    clients = ["TXR QA Client One"]
    if client_count == 2:
        clients.append("TXR QA Client Two")
    return {
        "action": "create_txr_1507_draft",
        "formCode": FORM_CODE,
        "formSourceId": SOURCE_ID,
        "clientNames": clients,
        "marketArea": "Collin and Denton Counties, Texas",
        "termStart": "2026-08-01",
        "termEnd": "2027-01-31",
        "serviceLevel": "full_services",
        "intermediary": "authorized",
        "signerPlan": "clients_and_associate",
        "formUseAttested": True,
        "compensation": {"purchasePercentage": "3"},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://www.homeofferflow.com")
    parser.add_argument("--access-token", default=os.environ.get("HOF_ACCESS_TOKEN"))
    parser.add_argument("--clients", type=int, choices=(1, 2), default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.access_token:
        parser.error("Use an existing Supabase access token via --access-token or HOF_ACCESS_TOKEN.")

    args.output_dir.expanduser().mkdir(parents=True, exist_ok=True)
    status, content_type, raw = _request(
        args.base_url,
        args.access_token,
        "/api/admin-dashboard",
        method="POST",
        body=_payload(args.clients),
    )
    if status >= 300 or "json" not in content_type.lower():
        raise RuntimeError(f"Draft creation returned HTTP {status} with content type {content_type!r}.")
    result = json.loads(raw.decode("utf-8"))
    agreement = result.get("agreement") or {}
    agreement_id = str(agreement.get("id") or "")
    if not agreement_id:
        raise RuntimeError("Draft response did not contain an agreement id.")

    preview_path = f"/api/admin-dashboard?preview_agreement={agreement_id}"
    preview_status, preview_type, preview = _request(args.base_url, args.access_token, preview_path)
    if preview_status >= 300 or "pdf" not in preview_type.lower():
        raise RuntimeError(f"Preview returned HTTP {preview_status} with content type {preview_type!r}.")

    pdf_path = args.output_dir.expanduser() / f"txr-1507-{args.clients}-client-private-preview.pdf"
    pdf_path.write_bytes(preview)
    report = {
        "ok": True,
        "form_code": FORM_CODE,
        "client_count": args.clients,
        "signer_plan": "clients_and_associate",
        "draft_id_present": True,
        "preview_pdf": str(pdf_path),
        "signing_sent": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    report_path = args.output_dir.expanduser() / f"txr-1507-{args.clients}-client-qa-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"QA failed: {exc}", file=sys.stderr)
        raise SystemExit(2)

