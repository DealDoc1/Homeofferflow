# Account-scoped legal acceptance — 2026-09-21

## Outcome

HomeOfferFlow now keeps each signed-in user's browser-side legal-acceptance
receipt separate. On a shared browser, one agent's completed acceptance can no
longer cause a later agent to skip recording their own immutable receipt and
then encounter a server-side checkout rejection.

The same signed-in user remains protected from duplicate inserts during normal
retries and page activity.

## Scope, privacy, and cost

- Server-side checkout enforcement remains authoritative and continues to
  verify the current policy acceptance for the authenticated user.
- The 60-day trial, $29 monthly renewal, displayed terms, Stripe checkout, and
  cancellation rules are unchanged.
- The change stores no new identity, transaction, or marketing data. It only
  scopes an existing browser-session marker to the authenticated user ID.
- No new database object, vendor, preview deployment, or recurring cost is
  introduced.

## Verification

- Source assertions cover the OnDemand enrollment, subscription checkout, and
  offer-wizard acceptance markers.
- A browser-runtime test signs in two identities in one simulated tab and
  verifies that the first user is deduplicated while the second user receives a
  separate acceptance insert.
- 96 focused legal, billing, and OnDemand tests pass.
- The complete local regression suite passes: 2,383 tests.
- Production verification remains part of the one coordinated post-reset
  release.
