#!/usr/bin/env python3
"""Validate an authenticated release-QA summary and its metadata-only reports.

This is intentionally offline. It reads the output of
``run_authenticated_release_qa.py`` and proves that the bundle contains the
expected form/client combinations, keeps brokerage-admin privacy flags false,
and records no signing side effect or sensitive transaction data. It does not
contact HomeOfferFlow, Supabase, SignWell, or any source vault.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FORMS = ("TXR-1501", "TXR-1506", "TXR-1507", "TXR-1508")
CLIENT_COUNTS = (1, 2)
EXPECTED_PLAN = {
    "TXR-1501": "clients_and_associate",
    "TXR-1506": "consumers_and_associate",
    "TXR-1507": "clients_and_associate",
    "TXR-1508": "associate_and_clients",
}
SENSITIVE_MARKERS = (
    "access_token",
    "authorization",
    "client one",
    "client two",
    "example street",
    "example, tx",
    "sourceurl",
    "source_url",
    "storagepath",
    "storage_path",
)
EMAIL_RE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")


def _errors_for_summary(summary_path: Path):
    errors: list[str] = []
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"could not read summary JSON: {exc}"], None

    if payload.get("ok") is not True:
        errors.append("summary ok must be true")
    if payload.get("signing_sent") is not False:
        errors.append("summary signing_sent must be false")

    privacy = ((payload.get("brokerage_admin") or {}).get("privacy") or {})
    for key in (
        "buyerDetailsIncluded",
        "propertyDetailsIncluded",
        "offerTermsIncluded",
        "documentContentsIncluded",
    ):
        if privacy.get(key) is not False:
            errors.append(f"brokerage privacy flag {key} must be false")

    items = payload.get("txr_previews")
    if not isinstance(items, list):
        return errors + ["txr_previews must be an array"], payload

    expected = {(form, count) for form in FORMS for count in CLIENT_COUNTS}
    observed = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"preview {index + 1} is not an object")
            continue
        form = item.get("form_code")
        count = item.get("client_count")
        pair = (form, count)
        if pair in observed:
            errors.append(f"duplicate preview combination: {form}/{count}")
        observed.add(pair)
        if pair not in expected:
            errors.append(f"unexpected preview combination: {form}/{count}")
        if item.get("draft_id_present") is not True:
            errors.append(f"{form}/{count} must record draft_id_present=true")
        if item.get("signing_sent") is not False:
            errors.append(f"{form}/{count} signing_sent must be false")
        if item.get("signer_plan") != EXPECTED_PLAN.get(form):
            errors.append(f"{form}/{count} has an unexpected signer plan")

        preview = item.get("preview_pdf")
        if not isinstance(preview, str) or not preview:
            errors.append(f"{form}/{count} is missing preview_pdf")
        else:
            preview_path = Path(preview).expanduser()
            if not preview_path.is_file():
                errors.append(f"{form}/{count} preview PDF does not exist: {preview}")
            elif preview_path.suffix.lower() != ".pdf":
                errors.append(f"{form}/{count} preview_pdf is not a PDF path")

        report_path = summary_path.parent / f"{str(form).lower()}-{count}-client-qa-report.json"
        if not report_path.is_file():
            errors.append(f"missing metadata report: {report_path.name}")
        else:
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid metadata report {report_path.name}: {exc}")
            else:
                if report.get("signing_sent") is not False:
                    errors.append(f"{report_path.name} signing_sent must be false")
                if report.get("signer_plan") != EXPECTED_PLAN.get(form):
                    errors.append(f"{report_path.name} signer plan mismatch")
                report_text = json.dumps(report, ensure_ascii=False).lower()
                for marker in SENSITIVE_MARKERS:
                    if marker in report_text:
                        errors.append(f"{report_path.name} contains sensitive marker {marker!r}")
                if EMAIL_RE.search(report_text):
                    errors.append(f"{report_path.name} contains an email address")

    missing = sorted(expected - observed)
    for form, count in missing:
        errors.append(f"missing preview combination: {form}/{count}")
    if len(items) != len(expected):
        errors.append(f"expected {len(expected)} previews, found {len(items)}")
    return errors, payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="authenticated-release-qa-summary.json")
    args = parser.parse_args(argv)
    errors, payload = _errors_for_summary(args.summary.expanduser())
    report = {
        "ok": not errors,
        "summary": str(args.summary.expanduser()),
        "expectedForms": list(FORMS),
        "expectedClientCounts": list(CLIENT_COUNTS),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if payload is not None and not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
