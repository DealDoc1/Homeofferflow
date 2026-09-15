# Homepage resume buttons and saved interview identity

Status: locally implemented and tested; not deployed or browser-verified.

## Customer outcome

The three homepage buttons could display "Resume Your Saved Offer" while
their actual `beginOfferFrom` click handler still called the fresh-start
reset. Those exact homepage surfaces now resume an accessible homebuyer
draft when one exists. Dedicated campaign/share/new-transaction entry
surfaces keep their existing behavior.

- Resume labels appear only for a matching homebuyer draft. When no matching
  draft remains, cached original labels/price note are restored without
  overwriting a subsequently selected audience's new copy.
- Generic local resume retains the role restored from the snapshot instead
  of forcing agent and investor interviews into homebuyer mode.
- A failed or unavailable resume no longer falls back to clearing the saved
  work and starting fresh. It returns a plain-language retry notice.
- Non-critical resume-event logging cannot throw after a successful restore.
- New visitors still start a new offer; explicit agent, investor, and seller
  homepage choices retain their dedicated routes.

Expected value: avoids an unintended restart for returning buyers and avoids
moving account offers to the wrong interview. No measured conversion lift
or production behavior claimed.

## Verification

Baseline: `cfb9c08b`.

- Saved-offer/local-entry runtime suite: 66 passed, with 15 new cases.
- Against the baseline: 11 failures reproduced; 55 positive controls passed.
- Tests execute the actual onclick strings from all three homepage buttons,
  plus the actual entry, local resume, snapshot restore, and calculation
  functions with mocked DOM/storage/navigation boundaries.
- Cases cover preservation of saved amounts and step, role identity,
  ownership mismatch, restoration failure, resume telemetry failure, new
  visitors, all dedicated audience routes, and stale-label recovery.
- Full suite: 1,998 passed in 16.336 seconds. Invalid fixture PDF diagnostic
  following `OK` is expected negative-case output, not a failing test.
- All 45 inline scripts parse; `git diff --check` passes.

## Release limits

No authenticated browser, live database, or production verification performed.
No customer messages, signatures, payments, documents, or external settings
changed. No GitHub publication or Vercel build/preview/deployment started.
No new dependency or recurring cost. Record in the daily report as locally
tested and awaiting release, not deployed.
