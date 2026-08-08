#!/usr/bin/env python3
"""Run the authenticated pre-release QA bundle without sending signatures.

This combines the read-only brokerage-admin privacy check with private TXR
preview generation. It requires an existing Supabase access token and never
creates a SignWell document. Preview PDFs and metadata-only reports are written
to the requested output directory so the reviewer can inspect every visible
field before any restricted form is activated.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import run_authenticated_txr_qa as txr_qa
import verify_brokerage_admin_live as admin_qa
import render_qa_pdf


def _parse_clients(value: str) -> list[int]:
    clients = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        count = int(item)
        if count not in (1, 2):
            raise ValueError("client counts must be 1 or 2")
        if count not in clients:
            clients.append(count)
    if not clients:
        raise ValueError("at least one client count is required")
    return clients


def run(base_url: str, token: str, output_dir: Path, forms: list[str], clients: list[int], *, render_pages: bool = False):
    output_dir.expanduser().mkdir(parents=True, exist_ok=True)
    status, admin_payload = admin_qa._get(base_url, token)
    admin_errors = (
        [f"Brokerage admin endpoint returned HTTP {status}."]
        if status >= 300
        else admin_qa.validate(admin_payload, "ondemand")
    )
    report = {
        "ok": not admin_errors,
        "base_url": base_url,
        "brokerage_admin": {
            "http_status": status,
            "errors": admin_errors,
            "privacy": admin_payload.get("privacy") if isinstance(admin_payload, dict) else {},
        },
        "txr_previews": [],
        "signing_sent": False,
    }

    for form in forms:
        for client_count in clients:
            payload = txr_qa._payload(form, client_count)
            status, content_type, raw = txr_qa._request(
                base_url,
                token,
                "/api/admin-dashboard",
                method="POST",
                body=payload,
            )
            if status >= 300 or "json" not in content_type.lower():
                raise RuntimeError(
                    f"{form} ({client_count} clients) draft returned HTTP {status} "
                    f"with content type {content_type!r}."
                )
            result = json.loads(raw.decode("utf-8"))
            agreement_id = str((result.get("agreement") or {}).get("id") or "")
            if not agreement_id:
                raise RuntimeError(f"{form} draft response did not contain an agreement id.")
            preview_status, preview_type, preview = txr_qa._request(
                base_url,
                token,
                f"/api/admin-dashboard?preview_agreement={agreement_id}",
            )
            if preview_status >= 300 or "pdf" not in preview_type.lower():
                raise RuntimeError(
                    f"{form} ({client_count} clients) preview returned HTTP {preview_status} "
                    f"with content type {preview_type!r}."
                )
            pdf_path = output_dir / f"{form.lower()}-{client_count}-client-private-preview.pdf"
            pdf_path.write_bytes(preview)
            report_path = output_dir / f"{form.lower()}-{client_count}-client-qa-report.json"
            item = {
                "form_code": form,
                "client_count": client_count,
                "signer_plan": payload.get("signerPlan"),
                "draft_id_present": True,
                "preview_pdf": str(pdf_path),
                "signing_sent": False,
            }
            if render_pages:
                render_dir = output_dir / f"{form.lower()}-{client_count}-client-rendered"
                render_qa_pdf.render(pdf_path, render_dir)
                item["render_manifest"] = str(render_dir / "render-manifest.json")
            report_path.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
            report["txr_previews"].append(item)

    report["ok"] = report["ok"] and bool(report["txr_previews"])
    summary_path = output_dir / "authenticated-release-qa-summary.json"
    summary_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://www.homeofferflow.com")
    parser.add_argument("--access-token", default=os.environ.get("HOF_ACCESS_TOKEN"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--forms",
        default=",".join(txr_qa.SOURCE_IDS),
        help="comma-separated TXR form codes (default: all supported forms)",
    )
    parser.add_argument(
        "--clients",
        default="1,2",
        help="comma-separated client counts, each 1 or 2 (default: 1,2)",
    )
    parser.add_argument("--render-pages", action="store_true", help="Render each private preview into page images for visual review.")
    args = parser.parse_args(argv)
    if not args.access_token:
        parser.error("Use an existing Supabase access token via --access-token or HOF_ACCESS_TOKEN.")
    forms = [form.strip().upper() for form in args.forms.split(",") if form.strip()]
    unknown = sorted(set(forms) - set(txr_qa.SOURCE_IDS))
    if unknown:
        parser.error(f"unsupported form code(s): {', '.join(unknown)}")
    try:
        clients = _parse_clients(args.clients)
        report = run(args.base_url, args.access_token, args.output_dir.expanduser(), forms, clients, render_pages=args.render_pages)
    except (RuntimeError, ValueError) as exc:
        print(f"Authenticated QA failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
