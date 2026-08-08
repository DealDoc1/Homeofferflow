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
separate release gate is approved. ``--form TREC-55-1`` creates a private
seller-disclosure draft with the approved TREC-61-0 water source attached;
that path also stops at an unsigned preview and never sends for signature.
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

try:
    from scripts import render_qa_pdf
except ModuleNotFoundError:  # pragma: no cover - supports direct script execution
    import render_qa_pdf


SOURCE_IDS = {
    "TXR-1501": "084958a8-fa91-498b-a31a-024f5a0dc310",
    "TXR-1506": "39970342-064d-478d-868e-3a0399db91f4",
    "TXR-1507": "016b54b3-61e9-4857-a048-f62f04fb8db9",
    "TXR-1508": "ec9f2965-36a9-4079-9255-6def587bc3d7",
}

SELLER_SOURCE_IDS = {
    "TREC-55-1": "49633253-590f-4c8d-b386-799df7f9ab3b",
    "TREC-61-0": "df32675f-95a1-435c-b1c3-a8db1ed08b56",
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


def _seller_disclosure_payload(seller_count: int):
    sellers = ["TXR QA Seller One"]
    if seller_count == 2:
        sellers.append("TXR QA Seller Two")
    return {
        "action": "create_seller_disclosure_draft",
        "formCode": "TREC-55-1",
        "disclosureSourceId": SELLER_SOURCE_IDS["TREC-55-1"],
        "waterSourceId": SELLER_SOURCE_IDS["TREC-61-0"],
        "propertyAddress": "100 Example Street, Example City, TX 75000",
        "sellerNames": sellers,
        "buyerNames": ["TXR QA Purchaser One"],
        "responseData": {},
        "waterRightsData": {},
    }


def _run_one(base_url: str, access_token: str, form: str, client_count: int, output_dir: Path, *, render_pages: bool = False):
    output_dir.expanduser().mkdir(parents=True, exist_ok=True)
    seller_disclosure = form == "TREC-55-1"
    draft_payload = (
        _seller_disclosure_payload(client_count)
        if seller_disclosure
        else _payload(form, client_count)
    )
    status, content_type, raw = _request(
        base_url,
        access_token,
        "/api/admin-dashboard",
        method="POST",
        body=draft_payload,
    )
    if status >= 300 or "json" not in content_type.lower():
        raise RuntimeError(f"Draft creation returned HTTP {status} with content type {content_type!r}.")
    result = json.loads(raw.decode("utf-8"))
    agreement = (result.get("draft") if seller_disclosure else result.get("agreement")) or {}
    agreement_id = str(agreement.get("id") or "")
    if not agreement_id:
        raise RuntimeError("Draft response did not contain an agreement id.")

    preview_path = (
        f"/api/admin-dashboard?preview_seller_disclosure={agreement_id}"
        if seller_disclosure
        else f"/api/admin-dashboard?preview_agreement={agreement_id}"
    )
    preview_status, preview_type, preview = _request(base_url, access_token, preview_path)
    if preview_status >= 300 or "pdf" not in preview_type.lower():
        raise RuntimeError(f"Preview returned HTTP {preview_status} with content type {preview_type!r}.")

    subject_count = "seller" if seller_disclosure else "client"
    pdf_path = output_dir.expanduser() / f"{form.lower()}-{client_count}-{subject_count}-private-preview.pdf"
    pdf_path.write_bytes(preview)
    report = {
        "ok": True,
        "form_code": form,
        "client_count": client_count,
        "signer_plan": None if seller_disclosure else draft_payload.get("signerPlan"),
        "seller_review_only": seller_disclosure,
        "water_source_attached": bool(seller_disclosure and draft_payload.get("waterSourceId")),
        "draft_id_present": True,
        "preview_pdf": str(pdf_path),
        "signing_sent": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if render_pages:
        render_dir = output_dir.expanduser() / f"{form.lower()}-{client_count}-{subject_count}-rendered"
        render_qa_pdf.render(pdf_path, render_dir)
        report["render_manifest"] = str(render_dir / "render-manifest.json")
    report_path = output_dir.expanduser() / (
        f"{form.lower()}-{client_count}-{subject_count}-qa-report.json"
    )
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://www.homeofferflow.com")
    parser.add_argument("--access-token", default=os.environ.get("HOF_ACCESS_TOKEN"))
    parser.add_argument(
        "--form",
        choices=tuple(SOURCE_IDS) + ("TREC-55-1", "ALL"),
        default="TXR-1507",
        help="Form to preview, or ALL for every supported TXR form plus TREC-55-1.",
    )
    parser.add_argument("--clients", type=int, choices=(1, 2), default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--render-pages", action="store_true", help="Render each private preview into page images for visual review.")
    args = parser.parse_args(argv)
    if not args.access_token:
        parser.error("Use an existing Supabase access token via --access-token or HOF_ACCESS_TOKEN.")

    forms = tuple(SOURCE_IDS) + ("TREC-55-1",) if args.form == "ALL" else (args.form,)
    reports = [
        _run_one(args.base_url, args.access_token, form, args.clients, args.output_dir / form.lower(), render_pages=args.render_pages)
        for form in forms
    ]
    print(json.dumps(reports[0] if len(reports) == 1 else {"ok": True, "reports": reports}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"QA failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
