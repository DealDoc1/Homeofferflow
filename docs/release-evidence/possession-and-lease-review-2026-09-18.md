# Possession and temporary-lease review — September 18, 2026

## Findings and local changes

- The buyer temporary-lease dropdown and introduction incorrectly described
  occupancy after closing. They now describe occupancy before closing. The
  introduction includes the form's 90-day scope and identifies Buyer as Tenant
  and Seller as Landlord.
- Verified the distinction against TREC's current official descriptions:
  https://www.trec.texas.gov/forms/buyers-temporary-residential-lease
  https://www.trec.texas.gov/forms/sellers-temporary-residential-lease
- The interview and account default labels now say "Upon closing and funding,"
  matching the renderer's non-lease election. The old `closing` option remains
  as a hidden compatibility option so saved values are not lost.
- The review no longer displays internal possession values. It shows a plain
  description, or "Not entered" for an unknown value, without mutating offer data.
- The selected temporary lease has its own concise review section covering
  start/termination date, daily/total rent as applicable, deposit, utilities,
  pets, holdover charges, and the complete entered special provisions. Inactive
  lease answers are not displayed. Existing editable answers remain intact.
- The selected temporary lease appears in the addendum list.
- For a seller temporary lease, the signing explanation reflects the actual
  purchase-contract and lease routing already implemented in the adapter.
  Buyer-only temporary-lease packets do not promise new Seller invitations.
- Comma-formatted amounts and zero amounts render correctly. Missing/invalid
  values are not displayed as fabricated zeroes or `$NaN`.
- Saved `leaseback` profile preferences now map to the existing
  `sellerTemporaryLease` interview option instead of an unmatched value.
  Defaults still do not overwrite an existing current choice.

## Verification

- Actual-source JavaScript runtime checks: **111 pass**, including the profile
  default safety suite and **38 offer-review checks**. New cases cover the
  readable possession labels, both lease review paths, simultaneous seller
  signing scope, stale answer removal, escaped text across lease fields,
  comma/zero/missing amounts, and the saved leaseback default.
- Updated the buyer temporary-lease regression to assert the official
  before-closing wording rather than preserving the incorrect wording.
- `git diff --check` passes.
- Full local suite: **2,049 tests; 2,047 pass, 2 fail in 20.322 seconds**.
  The only failures are the existing TXR-1507 map-reference comparisons:
  `test_every_current_map_matches_the_source_calibrated_baseline` and
  `test_current_released_maps_match_the_approved_baseline`. Their reference
  files are intentionally unchanged pending completed-provider verification.
- These are local runtime and source checks, not authenticated browser, visual
  responsive-layout, completed-provider, or production verification.

## Release status and follow-up

Local only. No push, deployment, provider request, customer email, signed-document
edit, PDF coordinate change, or Vercel build/preview usage. The separate TXR-1507
candidate still awaits fresh completed-provider QA; approved reference maps
remain unchanged.

Further observed review work: MUD/PID and lead-paint confirmation flags are still
listed under "Addenda Included" even though those flags alone do not attach a
document. Non-realty descriptions are still shortened in the review. Address
those mismatches separately; do not claim the entire review or all customer
paths are complete from the limited checks above.

Include the fixes as locally implemented/tested in the next daily report, with
no measured production conversion or revenue impact claimed.
