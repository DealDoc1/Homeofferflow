#!/usr/bin/env python3
"""Validate an authenticated seller QA summary without contacting services."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def errors_for_summary(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"could not read summary JSON: {exc}"]
    if payload.get("ok") is not True:
        errors.append("summary ok must be true")
    if payload.get("form_code") != "TREC-55-1":
        errors.append("form_code must be TREC-55-1")
    if payload.get("water_form_code") != "TREC-61-0":
        errors.append("water_form_code must be TREC-61-0")
    if payload.get("signing_sent") is not False:
        errors.append("signing_sent must be false")
    expected = {(1, "seller"), (2, "seller")}
    observed = set()
    reports = payload.get("reports")
    if not isinstance(reports, list):
        return errors + ["reports must be an array"]
    for report in reports:
        if not isinstance(report, dict):
            errors.append("each report must be an object")
            continue
        pair = (report.get("client_count"), "seller")
        observed.add(pair)
        if pair not in expected:
            errors.append(f"unexpected seller count: {report.get('client_count')}")
        if report.get("form_code") != "TREC-55-1":
            errors.append("report form_code must be TREC-55-1")
        if report.get("seller_review_only") is not True:
            errors.append("seller report must be review-only")
        if report.get("water_source_attached") is not True:
            errors.append("seller report must attach TREC-61-0")
        if report.get("draft_id_present") is not True:
            errors.append("seller report must record a draft id")
        if report.get("signing_sent") is not False:
            errors.append("seller report signing_sent must be false")
        preview = report.get("preview_pdf")
        if not isinstance(preview, str) or not preview or not Path(preview).is_file():
            errors.append("seller report preview_pdf must point to an existing PDF")
    for missing in sorted(expected - observed):
        errors.append(f"missing seller preview: {missing[0]}")
    if len(reports) != 2:
        errors.append(f"expected 2 seller reports, found {len(reports)}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args(argv)
    errors = errors_for_summary(args.summary.expanduser())
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
