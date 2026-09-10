#!/usr/bin/env python3
"""Guard every approved standalone TXR SignWell widget against coordinate drift.

The full purchase-packet renderer has its own page-image regression suite.
This companion check covers the released standalone TXR review-and-send forms.
It stores no client data or source PDFs: the committed baseline contains only
field identifiers, recipient roles, and the approved SignWell rectangles.

Use --write-baseline only after reviewing the matching source overlays and a
completed SignWell packet when the signing map changes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "tests" / "fixtures" / "txr_signwell_geometry_baseline.json"
GEOMETRY_KEYS = (
    "api_id",
    "type",
    "page",
    "x",
    "y",
    "width",
    "height",
    "recipient_id",
    "required",
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_baseline() -> dict:
    """Build the privacy-safe signing-map contract from current field builders."""
    from scripts.render_txr_signwell_map_review import review_field_sets

    return {
        "version": 1,
        "coordinate_system": "SignWell 96-DPI top-origin US Letter",
        "forms": {
            code: [
                {key: field.get(key) for key in GEOMETRY_KEYS}
                for field in sorted(fields, key=lambda value: str(value.get("api_id") or ""))
            ]
            for code, fields in sorted(review_field_sets().items())
        },
    }


def compare(actual: dict, expected: dict) -> tuple[bool, str]:
    if actual.get("version") != expected.get("version"):
        return False, "baseline version changed"
    if actual.get("coordinate_system") != expected.get("coordinate_system"):
        return False, "coordinate system changed"
    if set(actual.get("forms", {})) != set(expected.get("forms", {})):
        return False, "released form set changed"
    for code, current_fields in actual["forms"].items():
        approved_fields = expected["forms"][code]
        if current_fields != approved_fields:
            current_by_id = {field["api_id"]: field for field in current_fields}
            approved_by_id = {field["api_id"]: field for field in approved_fields}
            if set(current_by_id) != set(approved_by_id):
                return False, f"{code}: signing field set changed"
            for api_id, current in current_by_id.items():
                if current != approved_by_id[api_id]:
                    return False, f"{code}: {api_id} placement changed"
            return False, f"{code}: signer geometry changed"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write a candidate baseline after required source and signed-PDF review.",
    )
    args = parser.parse_args()
    actual = build_baseline()
    if args.write_baseline:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Wrote {BASELINE_PATH.relative_to(ROOT)}")
        return 0
    expected = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    matches, reason = compare(actual, expected)
    if not matches:
        raise SystemExit(
            "TXR SignWell signer geometry changed: "
            + reason
            + ". Review source overlays and a completed packet before updating the baseline."
        )
    print("TXR SignWell signer geometry matches the approved baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
