# AI calibration record validation

`scripts/validate_ai_calibration_records.py` validates the eventual five
anonymized broker/agent review records before they are treated as calibration
evidence. It is an evidence-shape and privacy check only; it does not approve
new scoring, wording, or model behavior.

The input must be either a JSON array or an object with a `reviews` array. It
must contain exactly these scenario IDs:

```text
AI-CAL-01, AI-CAL-02, AI-CAL-03, AI-CAL-04, AI-CAL-05
```

Each record must include the structured reviewer fields documented in
`AI_OFFER_REVIEW_CALIBRATION_REVIEWER_PACKET.md`. Reviewer roles are limited to
`broker` or `agent`; dispositions are `useful`, `needs_revision`, or
`unsafe_until_revised`.

The validator rejects missing scenarios, missing structured fields, duplicate
IDs, invalid dispositions, non-boolean disclaimer/overclaiming fields, and
obvious identifying data such as email addresses, phone numbers, MLS markers,
or exact street-address markers.

Run locally after collecting the anonymized records:

```bash
python scripts/validate_ai_calibration_records.py path/to/ai-calibration-records.json
```

A passing validation report still does not activate calibration. The five
records must be independently reconciled, any disagreements documented, and
product release authority must approve any scoring or wording change.
