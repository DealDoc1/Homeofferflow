# Browser-saved draft isolation and amount preservation

Status: locally implemented and tested; not deployed or browser-verified.

## Customer outcome

- New browser snapshots include only controls inside the offer interview,
  excluding file and password inputs. They no longer capture account/admin
  or unrelated form fields elsewhere on the page.
- Restoring a draft replaces the prior interview's fields and transaction
  state. Restored numeric answers are marked as intentional, so the price and
  financing calculators do not silently replace saved amounts or zero values.
- Named checkbox groups, including leased/assumed fixture choices without
  individual element IDs, now round-trip. Fixture collection and radio-card
  presentation are scoped to the interview rather than other open forms.
- New snapshots retain the existing offer ID; restore uses it only with the
  existing matching-owner boundary. Legacy snapshots without an ID start
  without one instead of inheriting another open offer's ID. This client
  metadata does not replace the existing server/database ownership checks.
- Restored transaction role is set before choosing the saved step. The
  current interview's signing artifacts cannot carry into the restored state.
- Only attachment names are retained as re-upload cues; file contents from
  another transaction and the old attachment acknowledgment are cleared.
- Legacy snapshots may still contain unrelated field IDs or fake file paths;
  restore ignores them. Existing stored snapshots are not proactively erased.
- Malformed snapshot shapes leave the current interview unchanged. The
  restore-in-progress flag returns synchronously to its previous value,
  removing the delayed flag reset that could affect subsequent work.

## Verification

Baseline: `f9179baa`.

- Saved-offer/browser-draft runtime suite: 51 passing cases, 14 added here.
- Against the baseline: 12 failures reproduced; 39 controls passed.
- Tests execute actual snapshot, restore, collection, field reset, attachment
  reset, and calculation functions with mocked DOM/storage/provider boundaries.
- Cases cover all three purchase-interview roles, zero/custom financing
  values, unrelated page fields, legacy file-path assignment, grouped fixture
  choices with a same-named external form, owner mismatch/anonymous metadata,
  malformed inputs, attachment isolation, and restore-flag timing.
- Full suite: 1,997 passed in 16.298 seconds. Expected invalid fixture PDF
  diagnostic following `OK` is negative-case output, not a failing test.
- All 45 inline scripts parse; `git diff --check` passes.

## Release limits

No authenticated browser, live database, or production verification performed.
No customer messages, signatures, payments, documents, or external settings
changed. No GitHub publication or Vercel build/preview/deployment started.
No new dependency, service, or recurring cost. Record in the daily report as
locally tested and awaiting release, not deployed.
