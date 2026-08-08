# AI offer-review calibration bundle - 2026-08-08

## What was completed

`scripts/build_ai_calibration_review_bundle.py` now produces a clean reviewer
bundle containing the five existing anonymized AI-CAL scenarios, deterministic
technical baselines, the worksheet, payload guidance, and a blank structured
review-record template.

The bundle is explicitly **not calibration evidence**. It does not call the AI
endpoint, change scoring or wording, or mark the roadmap item passed.

## Review gate still required

Five independent reviews by currently practicing Texas real-estate brokers or
agents must still be completed and submitted through the authenticated review
path. The records must remain anonymized and include a disposition for each of
AI-CAL-01 through AI-CAL-05. Only then may scoring or wording changes be
considered, followed by the existing regression and release gates.

## Verification

- Bundle builder completed successfully.
- `tests.test_ai_calibration_review_bundle`: passed.
- The production AI behavior remains unchanged.
