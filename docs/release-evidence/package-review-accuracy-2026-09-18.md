# Package review accuracy — September 18, 2026

## Defects and local changes

- MUD/PID and pre-1978/unknown-year answers appeared as selected entries under
  "Addenda Included" even though those answers do not attach disclosure PDFs.
  Removed those entries from the document list. Keep lead-paint status in the
  disclosure summary and show district notice follow-up there as well.
- The district interview's "not sure" answer promised to include a disclosure.
  It now asks the user to confirm district status with the listing side; the
  helper and review explain that notices must be uploaded to include them.
  This is a description of application behavior, not a determination of which
  statutory disclosures apply to a particular property.
- The document list now includes the base purchase contract and only selected
  addenda/uploads, without the long list of dimmed, unselected choices.
- Appraisal terms and the appraisal-addendum entry follow the renderer's
  current canonical financing/selection rules. A stale choice after switching
  to cash, FHA, or VA is not represented as an included appraisal addendum.
- Non-realty descriptions are displayed in full, with wrapping, line breaks,
  and escaped markup. Zero consideration displays as `$0`. Missing descriptions
  stay visibly incomplete rather than claiming an included non-realty addendum.
- Uploaded documents remain identifiable by their supplied filenames; a
  district/lead answer alone never creates an uploaded-document entry.

## Verification

- **46 actual-source JavaScript review checks pass**, including eight new cases
  and an updated full-description regression.
- Run the same tests against the previous HEAD using `HOF_TEST_SOURCE_REF=HEAD`:
  **nine checks fail against the old behavior**. This independently
  demonstrates the removed truncation and false package-list claims.
- Replaced a source assertion tied to the former ternary expression with the
  new formatting expression, retaining the blank-amount requirement. Actual
  runtime tests separately cover blank, null, undefined, numeric zero, and
  string zero; this was not a removal of the behavior check.
- The appraisal case exercises all 25 combinations of five current financing
  choices and five appraisal selections, including an unknown selection.
- Checked the display conditions against `lib/verified_20_19.py`'s actual
  `has_appraisal` and `has_non_realty` predicates, and its explicit attachment
  handling. Legacy imported aliases outside the current interview are not
  comprehensively verified by this matrix.
- `git diff --check` passes. Browser/responsive visual QA and production behavior
  remain unverified; no claim of end-to-end completion.
- Full local suite: **2,049 tests; 2,047 pass, 2 fail in 19.794 seconds**.
  The only remaining failures are the existing TXR-1507 map-reference checks:
  `test_every_current_map_matches_the_source_calibrated_baseline` and
  `test_current_released_maps_match_the_approved_baseline`. Their approved
  reference files remain unchanged pending completed-provider verification.

## Release status and next work

Local only. No deployment, Git push, provider API call, customer email, database
mutation, or Vercel build/preview usage. No source PDF or signature coordinates
changed. Keep the separate TXR-1507 completed-provider QA requirement visible.

The non-realty **review** now preserves all entered items. The generated
non-realty form still uses a separate three-line renderer limit; full PDF
overflow handling is a distinct remaining task. Do not report this UI change
as correcting generated-PDF truncation.

Include this work in the next daily report as local implementation/test results,
not deployed functionality or measured conversion/revenue improvement.
