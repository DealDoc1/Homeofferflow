#!/usr/bin/env python3
"""Create and download a private TXR preview for authenticated QA.

This helper never sends a SignWell document. It uses an existing Supabase
access token, creates a private draft through the authenticated production
API, downloads the private preview PDF, and writes a metadata-only report.
No client names, addresses, compensation values, tokens, or source URLs are
written to the report.

Usage::

    HOF_ACCESS_TOKEN='...' python scripts/run_authenticated_txr_qa.py \
      --form TXR-1507 --output-dir /tmp/txr-1507-qa --clients 1

Use ``--clients 2`` for the two-client signer-plan scenario. The same helper
supports TXR-1501, TXR-1508, and TXR-1506 so each form can be QA'd before its
separate release gate is approved.
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


SOURCE_IDS = {
    "TXR-1501": "084958a8-fa91-498b-a31a-024f5a0dc310",
    "TXR-1506": "39970342-064d-478d-868e-3a0399db91f4",
    "TXR-1507": "016b54b3-61e9-4857-a048-f62f04fb8db9",
    "TXR-1508": "ec9f2965-36a9-4079-9255-6def587bc3d7",
}


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


def _payload(form_code: str, client_count: int):
    clients = ["TXR QA Client One"]
    if client_count == 2:
        clients.append("TXR QA Client Two")
    common = {
        "formCode": form_code,
        "formSourceId": SOURCE_IDS[form_code],
        "clientNames": clients,
        "formUseAttested": True,
    }
    if form_code == "TXR-1507":
        return {
            **common,
            "action": "create_txr_1507_draft",
            "marketArea": "Collin and Denton Counties, Texas",
            "termStart": "2026-08-01",
            "termEnd": "2027-01-31",
            "serviceLevel": "full_services",
            "intermediary": "authorized",
            "signerPlan": "clients_and_associate",
            "compensation": {"purchasePercentage": "3"},
        }
    if form_code == "TXR-1501":
        return {
            **common,
            "action": "create_txr_1501_draft",
            "clientAddress": "100 Example Street",
            "clientCityStateZip": "Example, TX 75000",
            "clientPhone": "0000000000",
            "clientEmail": "txr-qa@example.invalid",
            "marketArea": "Collin and Denton Counties, Texas",
            "termStart": "2026-08-01",
            "termEnd": "2027-01-31",
            "paymentCounty": "Collin",
            "intermediary": "authorized",
            "signerPlan": "clients_and_associate",
            "compensation": {"purchasePercentage": "3"},
        }
    if form_code == "TXR-1508":
        return {
            **common,
            "action": "create_txr_1508_draft",
            "propertyAddress": "100 Example Street, Example City, TX 75000",
            "otherBrokerAgreement": ["no"] * client_count,
            "unrepresentedAcknowledgment": True,
            "signerPlan": "associate_and_clients",
        }
    return {
        **common,
        "action": "create_txr_1506_draft",
        "consumerRole": "buyer",
        "additionalNotice": "Please review and ask questions before signing.",
        "noticeAcknowledgment": True,
        "signerPlan": "consumers_and_associate",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://www.homeofferflow.com")
    parser.add_argument("--access-token", default=os.environ.get("HOF_ACCESS_TOKEN"))
    parser.add_argument("--form", choices=tuple(SOURCE_IDS), default="TXR-1507")
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
        body=_payload(args.form, args.clients),
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

    pdf_path = args.output_dir.expanduser() / f"{args.form.lower()}-{args.clients}-client-private-preview.pdf"
    pdf_path.write_bytes(preview)
    report = {
        "ok": True,
        "form_code": args.form,
        "client_count": args.clients,
        "signer_plan": "clients_and_associate",
        "draft_id_present": True,
        "preview_pdf": str(pdf_path),
        "signing_sent": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    report_path = args.output_dir.expanduser() / f"{args.form.lower()}-{args.clients}-client-qa-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"QA failed: {exc}", file=sys.stderr)
        raise SystemExit(2)

