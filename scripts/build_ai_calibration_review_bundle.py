#!/usr/bin/env python3
"""Build a clean, anonymized reviewer bundle for AI calibration.

This command packages the existing five deterministic scenarios and blank
review-record template for an independent Texas broker/agent review. It does
not call the AI endpoint, change scoring, or create calibration evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_FIXTURES.json"
BASELINE = ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_BASELINE.json"
WORKSHEET = ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_WORKSHEET.md"
PAYLOADS = ROOT / "docs" / "AI_OFFER_REVIEW_CALIBRATION_PAYLOADS.md"
OUTPUT_DEFAULT = ROOT / "docs" / "ai-calibration-review-bundle"

SCENARIO_IDS = ("AI-CAL-01", "AI-CAL-02", "AI-CAL-03", "AI-CAL-04", "AI-CAL-05")


def _blank_record(scenario_id: str) -> dict:
    return {
        "scenario_id": scenario_id,
        "review_date": "",
        "reviewer_role": "agent",
        "displayed_score": None,
        "displayed_market_mode": "",
        "displayed_source_model": "",
        "useful_output": "",
        "misleading_or_unsafe": "",
        "insufficient_or_missing": "",
        "disclaimer_clear": False,
        "overclaiming_or_advice": False,
        "recommended_change": "",
        "disposition": "needs_revision",
    }


def build(output_dir: Path) -> Path:
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    fixture_ids = tuple(item.get("id") for item in fixtures.get("scenarios", []))
    baseline_ids = tuple((baseline.get("scenarios") or {}).keys())
    if fixture_ids != SCENARIO_IDS or baseline_ids != SCENARIO_IDS:
        raise ValueError("Calibration fixtures and baseline must contain exactly AI-CAL-01 through AI-CAL-05.")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "fixtures.json").write_text(
        json.dumps(fixtures, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "technical-baseline.json").write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "review-record-template.json").write_text(
        json.dumps({"reviews": [_blank_record(item) for item in SCENARIO_IDS]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "worksheet.md").write_text(WORKSHEET.read_text(encoding="utf-8"), encoding="utf-8")
    (output_dir / "payloads.md").write_text(PAYLOADS.read_text(encoding="utf-8"), encoding="utf-8")
    (output_dir / "README.md").write_text(
        """# AI offer-review calibration bundle

This bundle contains five anonymized scenarios for independent review by a
currently practicing Texas real-estate broker or agent. The technical
baseline is not calibration evidence. Complete one review record per
scenario, keep facts anonymized, and submit the records through the
authenticated feedback flow or the internal QA process.

Do not change AI scoring, wording, or release status from this bundle.
Five completed independent reviews and documented dispositions are
required before calibration changes or broader claims.

Files:

- `fixtures.json`: the five scenario facts.
- `technical-baseline.json`: deterministic fallback output for comparison.
- `review-record-template.json`: blank anonymized records to complete.
- `worksheet.md`: reviewer instructions and release-gate record.
- `payloads.md`: copy/paste payload guidance for authenticated review.
""",
        encoding="utf-8",
    )
    return output_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args(argv)
    output = build(args.output_dir)
    try:
        label = output.relative_to(ROOT)
    except ValueError:
        label = output
    print(f"Wrote anonymized AI calibration bundle to {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
