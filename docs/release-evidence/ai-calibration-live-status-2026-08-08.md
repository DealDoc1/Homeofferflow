# AI offer-review calibration live status — 2026-08-08

## Current production state

The AI offer-review calibration gate remains intentionally closed. Production
review output is still educational review material and is not treated as
calibration evidence.

## Live evidence

The production Supabase project was queried for authenticated, anonymized
calibration records grouped by `calibration_scenario`. The result was an empty
set: no records are currently present for `AI-CAL-01` through `AI-CAL-05`.

The application and validator continue to require one valid human review for
each documented scenario before any scoring, wording, or calibration change is
allowed.

## Decision

No AI scoring or wording change was made in this release window. Existing
review behavior remains unchanged and covered by the regression suite.

## Next evidence required

Collect one anonymized human review for each of:

- `AI-CAL-01`
- `AI-CAL-02`
- `AI-CAL-03`
- `AI-CAL-04`
- `AI-CAL-05`

Reviews must omit names, exact addresses, MLS numbers, phone numbers, email
addresses, and other identifying transaction details. After collection, run
`scripts/validate_ai_calibration_records.py` and perform a separate review of
the proposed calibration changes before changing production scoring or copy.

