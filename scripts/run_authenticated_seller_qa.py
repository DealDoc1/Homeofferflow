#!/usr/bin/env python3
"""Run the authenticated seller-disclosure preview matrix without signing.

This is intentionally separate from the buyer/TXR matrix. It creates private
TREC-55-1 drafts for one- and two-seller scenarios, attaches the approved
TREC-61-0 source, downloads unsigned previews, and writes metadata-only QA
reports. It never creates a SignWell document.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from scripts import run_authenticated_txr_qa as qa
except ModuleNotFoundError:  # pragma: no cover - supports direct script execution
    import run_authenticated_txr_qa as qa


def _parse_sellers(value: str) -> list[int]:
    counts: list[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        count = int(raw)
        if count not in (1, 2):
            raise ValueError("seller counts must be 1 or 2")
        if count not in counts:
            counts.append(count)
    if not counts:
        raise ValueError("at least one seller count is required")
    return counts


def _assert_seller_sources_ready(base_url: str, token: str):
    """Fail closed unless both approved seller sources are ready live."""
    status, content_type, raw = qa._request(
        base_url,
        token,
        "/api/admin-dashboard?scope=brokerage",
    )
    if status >= 300 or "json" not in content_type.lower():
        raise RuntimeError(
            f"Seller source preflight returned HTTP {status} with content type {content_type!r}."
        )
    payload = json.loads(raw.decode("utf-8"))
    readiness = {
        str(item.get("formCode") or ""): item
        for item in (payload.get("sourceReadiness") or [])
    }
    missing = [
        code
        for code in ("TREC-55-1", "TREC-61-0")
        if (readiness.get(code) or {}).get("readyForRestrictedDraft") is not True
    ]
    if missing:
        raise RuntimeError(
            "Seller source preflight is not ready for: "
            + ", ".join(missing)
            + ". Confirm approval and attestation before creating seller previews."
        )


def run(base_url: str, token: str, output_dir: Path, seller_counts: list[int], *, render_pages: bool = False):
    output_dir.expanduser().mkdir(parents=True, exist_ok=True)
    _assert_seller_sources_ready(base_url, token)
    reports = [
        qa._run_one(
            base_url,
            token,
            "TREC-55-1",
            seller_count,
            output_dir.expanduser(),
            render_pages=render_pages,
        )
        for seller_count in seller_counts
    ]
    summary = {
        "ok": True,
        "base_url": base_url,
        "form_code": "TREC-55-1",
        "water_form_code": "TREC-61-0",
        "seller_counts": seller_counts,
        "reports": reports,
        "signing_sent": False,
        "source_ids": {
            "disclosure": qa.SELLER_SOURCE_IDS["TREC-55-1"],
            "water": qa.SELLER_SOURCE_IDS["TREC-61-0"],
        },
    }
    summary_path = output_dir.expanduser() / "authenticated-seller-qa-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://www.homeofferflow.com")
    parser.add_argument("--access-token", default=os.environ.get("HOF_ACCESS_TOKEN"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--sellers",
        default="1,2",
        help="comma-separated seller counts, each 1 or 2 (default: 1,2)",
    )
    parser.add_argument("--render-pages", action="store_true", help="Render each private preview into page images for visual review.")
    args = parser.parse_args(argv)
    if not args.access_token:
        parser.error("Use an existing Supabase access token via --access-token or HOF_ACCESS_TOKEN.")
    try:
        seller_counts = _parse_sellers(args.sellers)
        summary = run(args.base_url, args.access_token, args.output_dir, seller_counts, render_pages=args.render_pages)
    except (RuntimeError, ValueError) as exc:
        print(f"Authenticated seller QA failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
