#!/usr/bin/env python3
"""Validate the anonymized human-review records for AI calibration.

This validates evidence shape and anonymization only. It never changes model
scoring, wording, or the production calibration state.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = ("AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05")
REQUIRED_FIELDS = (
    "scenario_id",
    "review_date",
    "reviewer_role",
    "displayed_score",
    "displayed_market_mode",
    "displayed_source_model",
    "useful_output",
    "misleading_or_unsafe",
    "insufficient_or_missing",
    "disclaimer_clear",
    "overclaiming_or_advice",
    "recommended_change",
    "disposition",
)
ALLOWED_ROLES = {"broker", "agent"}
ALLOWED_DISPOSITIONS = {"useful", "needs_revision", "unsafe_until_revised"}
EMAIL_RE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)")
PII_MARKERS = ("mls", "client name", "client_name", "street address", "exact address")


def _as_reviews(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("reviews"), list):
        return payload["reviews"]
    raise ValueError("records must be a JSON array or an object containing a reviews array")


def _review_count(payload):
    try:
        return len(_as_reviews(payload))
    except ValueError:
        return 0


def _record_text(record):
    return json.dumps(record, ensure_ascii=False).lower()


def validate(payload):
    errors = []
    try:
        reviews = _as_reviews(payload)
    except ValueError as exc:
        return [str(exc)]
    by_id = {}
    for index, record in enumerate(reviews):
        if not isinstance(record, dict):
            errors.append(f"review {index + 1} is not an object")
            continue
        scenario_id = record.get("scenario_id")
        if scenario_id in by_id:
            errors.append(f"duplicate scenario_id: {scenario_id}")
        by_id[scenario_id] = record
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            errors.append(f"{scenario_id or '(missing scenario_id)'} missing: {', '.join(missing)}")
        if record.get("reviewer_role") not in ALLOWED_ROLES:
            errors.append(f"{scenario_id or '(missing scenario_id)'} has an invalid reviewer_role")
        if record.get("disposition") not in ALLOWED_DISPOSITIONS:
            errors.append(f"{scenario_id or '(missing scenario_id)'} has an invalid disposition")
        for field in ("disclaimer_clear", "overclaiming_or_advice"):
            if not isinstance(record.get(field), bool):
                errors.append(f"{scenario_id or '(missing scenario_id)'} {field} must be boolean")
        text = _record_text(record)
        if EMAIL_RE.search(text) or PHONE_RE.search(text) or any(marker in text for marker in PII_MARKERS):
            errors.append(f"{scenario_id or '(missing scenario_id)'} contains identifying transaction data")
    missing_ids = [scenario_id for scenario_id in EXPECTED_IDS if scenario_id not in by_id]
    unexpected_ids = [scenario_id for scenario_id in by_id if scenario_id not in EXPECTED_IDS]
    if missing_ids:
        errors.append("missing required scenarios: " + ", ".join(missing_ids))
    if unexpected_ids:
        errors.append("unexpected scenarios: " + ", ".join(str(item) for item in unexpected_ids))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path, help="JSON file containing the five anonymized review records")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.records.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Calibration records invalid: {exc}", file=sys.stderr)
        return 2
    errors = validate(payload)
    report = {
        "ok": not errors,
        "scenarioCount": _review_count(payload),
        "requiredScenarioIds": list(EXPECTED_IDS),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
