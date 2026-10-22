# Listing agreement notice contacts - October 17, 2026

## Scope and release boundary

Outcome: an agent reviews saved office notice details, supplies missing details
without a brokerage seat, and keeps those details with the listing agreement.
Scope: the TXR-1101 interview, authenticated context read, answer contract,
page-one contact overlay, Google address companion fields and focused tests.

Production baseline remains `7b408eb09b46720261e8fed4712fe42e81547f33`,
release `39028545771`. The preceding local checkpoint is
`36dde75d07283c551a6fda4e143469be4c79ade2`. This batch is **locally implemented,
tested and visually reviewed, not deployed or production-verified**.
Automatic Git deployments remain disabled. No preview build was requested.

## Behavior

- A verified-session, no-store GET returns only the current agent's brokerage
  name/license and five allowed notice-contact defaults. Active linked-office
  defaults remain optional; independent agents can enter contacts manually.
  A failed optional-default read does not prevent opening the interview.
- The listing context honors the existing administrator-approved shared-agent
  profile mapping. It never accepts a browser-selected profile owner. Account,
  organization membership and document ownership remain bound to the actual
  authenticated login. Non-listing professional-context behavior is unchanged.
- Brokerage name, broker license and associate identity remain account-derived.
  Editable notice contacts cannot change a profile, membership, broker signer
  or signing invitation recipient. OnDemand's existing blank-license fallback
  remains 9010832; the associate license is not used as the broker license.
- New drafts take current contact defaults. Saved drafts retain their nested
  contact snapshot, including intentionally cleared values. An explicit
  "Use current office details" action replaces that snapshot in the interview;
  it does not update the account or another agreement.
- The strict nested answer object accepts only address, city/state/ZIP, phone
  and two emails, with matching browser/server limits and email validation.
  Legacy drafts without the object retain their previous context fallback.
- Page one prints the document snapshot. Long or Unicode values use the
  existing lossless answer continuation and continuation initials. Overlay
  revision is now `txr-1101-2026-06-15-overlay-v2`; signer geometry is unchanged.
- Seller and brokerage mailing addresses use the existing Google completion
  bridge. Selecting an address updates only its corresponding city/state/ZIP,
  preserves units and clears missing components rather than keeping old data.
  The isolated browser fixture does not make paid Google requests; actual
  suggestion-service behavior was not exercised in this pass.

## Focused verification

67 Python checks passed, no skips, with the exact private source enabled:

```sh
HOF_TXR1101_SOURCE=/path/to/private/TXR-1101-2026-06-15.pdf \
python -m unittest tests.test_txr_1101 tests.test_txr1101_api \
  tests.test_txr1101_interview_runtime \
  tests.test_google_address_components_runtime \
  tests.test_google_address_autocomplete_coverage -q
```

46 JavaScript cases passed (26 listing, 20 Google component cases):

```sh
node --test tests/txr1101_interview.runtime.cjs \
  tests/google_address_components.runtime.cjs
```

Coverage includes the actual API handlers with isolated PostgREST/SignWell
transports, trusted shared-profile lookup, wrong-row/malformed-alias rejection,
unchanged older-form context, actor-bound office membership, saved blank
contacts, recipient separation and stale-account response rejection.
JavaScript syntax checks and `git diff --check` passed. This is an affected
workflow check, not the frozen release's full regression suite.

The read-only production query confirmed the owner's existing approved alias;
direct and shared agent name/license/brokerage values currently agree. No SQL
write, alias assignment, permission or schema change was made in this batch.

## Visual checks actually completed

The reproducible fixture uses the actual interview and prepared-document queue,
fictional identity/data, an isolated simulated API and external connections
blocked by CSP. Desktop and 390 x 844 phone checks covered:

- saved contact snapshot winning over different current defaults;
- explicit current-office reset;
- manually edited address and cleared email surviving same-ID save/reopen;
- optional-default failure with working manual entry and forward/back navigation;
- readable contact fields, no horizontal page overflow (390/390), and no
  browser error/warning entries in the inspected local run.

Screenshots are retained outside Git under the persistent chat output root:
`txr1101-notice-ui-qa-2026-10-17/desktop-saved-contact.png`,
`desktop-manual-fallback.png` and `mobile-saved-contact.png`.
They show **local fictional QA**, not live placements.

`scripts/render_txr1101_notice_qa.py` generated three fictional placement-guide
PDFs from exact source SHA-256
`eeec91ef481059834262cf7f842afc045bf17c09b5be9e79fe2508112310b068`.
All five changed-page images were visually reviewed: ordinary two-seller page
one, blank-contact/single-Unicode-seller page one, Unicode-overflow page one,
the page-eight continuation reference and page eleven's full continuation.
No clipping or overlapping contact text was observed. Source files and private
QA artifacts are outside Git at `txr1101-notice-qa-2026-10-17/`.
These are placement guides, **not completed SignWell PDFs**.

## Remaining release work

The missing independent-office contact collection is now locally completed.
Related-document package assembly, private source registration, coordinated
allowlist/readiness migration and readback, completed-provider signing/PDF QA,
shell version bump, frozen full regression, green exact-head CI and one
spend-checked intentional production release remain. Do not describe the
Paragraph 19 checklist as proof that those documents are attached. Do not
bundle unfinished disclosure PR 1341 or change its QA status in this batch.

No customer packets, provider invitations, emails, charges, subscriptions or
account permissions were created or changed. No owner action is needed to
continue the remaining engineering work.
