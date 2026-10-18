# Listing lead disclosure: isolated QA-only release

## Release contract

- Outcome: make the fixed owner-only lead-disclosure QA action available through
  the existing production signing connection, without exporting its credential.
- Baseline: production/main `7b408eb09b46720261e8fed4712fe42e81547f33`.
- Candidate: `codex/listing-lead-provider-qa`, isolated from the unfinished
  `codex/txr1101-sale-listing` development stack. The latter remains backed up.
- Scope: the fixed TREC 56-0 test builder, two small unconnected helper modules,
  optional QA-draft verification, action-only owner API/control, static source
  bundle inclusion and shell cache v106. No customer renderer, customer signing
  map, form eligibility, contract package or interview path is activated/changed.
- Exclusions: TXR-1101 source registration/migration/customer interview, saved
  listing packet integration and disclosure draft PR #1341. No SQL migration,
  permission change, source-owner requirement or brokerage-seat requirement.
- Release authority: the owner's standing direction to implement, push, merge
  and intentionally deploy the agreed work; no email to a third party or real
  customer invitation is part of this release.

## Source, signing plan and review boundary

The existing bundled public TREC 56-0 source remains byte-identical, pinned to
SHA-256 `eb8bdfb943cafbe8402e6b44fe44d73eb66d6acd6a99f31f73498f938fd76e6c`.
There is no new source PDF in Git. Four fictional cases produce seven pages,
42 reviewed fields, four exact-one checkbox groups and four conditional
explanation requirements. Only the two previously approved QA inboxes may be
used. Test mode, parallel invitations and disabled reminders are fixed.

Local seven-page visual review and desktop/390-pixel owner-control review are
complete, recorded in the [preparation evidence](listing-lead-provider-qa-preparation-2026-10-17.md).
The provider test has **not** run. Rendered signed-PDF QA remains the purpose of
this protected action, not a fabricated prerequisite pass. This release does
not declare customer lead-disclosure or TXR-1101 signing ready.

The new completion-control mode reserves the attempt before provider creation,
saves its exact draft identity before inspecting, verifies retained geometry,
recipients and rules, and saves the pre-send state before its sole send request.
Changed/missing settings, checkpoint failures and ambiguous provider outcomes
never create a replacement test. Existing purchase/showing/amendment QA paths
do not opt into this mode; their regression tests remain unchanged.

## Cost and release constraints

Git-triggered Vercel deployment remains disabled. No preview is requested. The
explicit HomeOfferFlow project/team was verified. The current September 22–
October 21 usage read reports $0.044601 in infrastructure charges excluding the
$20 Pro plan line, below the existing $17 release threshold/$3 reserve. The
production workflow must repeat its current spend/deployment-frequency check
immediately before the single intentional prebuilt release. No paid add-on,
new service, subscription, credential or polling loop is introduced.

## Candidate verification

The isolated candidate passes 85 focused tests, including the existing signing
QA paths and nine JavaScript control cases. The one future-listing request-
fingerprint test was excluded along with its unrelated customer delivery
change; the QA reservation binds its own layout and controls digests.

Frozen local regression: **2,679 tests, OK, one skipped**, in 88.207 seconds.
The expected mocked preflight/transport failures printed by negative tests are
not production errors. The cross-platform golden packet visual comparison,
approved TXR signer-geometry baseline and Supabase branch preflight (118
migrations, zero errors) pass. Patch whitespace is clean. Neither previously
reviewed helper dependency differs from `fcbf606`.

The one skipped legacy test mistook an ordinary CSS separator for unresolved
merge markers. Its guard now checks complete marker lines and fails rather
than silently skipping. Four focused manual-placement UI tests pass, including
the original script-inclusion assertion and the new false-positive guard case.
This strengthens test coverage without changing customer placement behavior.

Exact-head CI, production identity and canonical live owner-control verification
are recorded below when observed. Do not infer those results, actual provider
completion or customer-form release from the local regression pass.
