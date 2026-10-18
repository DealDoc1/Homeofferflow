# Listing lead disclosure: protected provider-QA preparation

## Scope and evidence boundary

Outcome pursued: actual provider verification of the new seller-side TREC 56-0
completion controls and final PDF, using fictional information and only the
owner's two approved test inboxes. This checkpoint prepares that live path;
**it does not claim the provider test has run or passed**.

The clean starting development head was
`fcbf606c19662af45793eb662df6329f44ee43ab`. The latest successful production
release remains run `39028545771` at
`7b408eb09b46720261e8fed4712fe42e81547f33`, freshly read from GitHub. No
production deployment, migration, signing invitation or customer mutation
occurred in this batch. This is not an additional customer access requirement.

## Connection investigation

- The existing SignWell Google login restored the same account. The document
  list showed 148 existing documents. No document was opened, edited or resent.
- GitHub repository/environment secret **names only** confirm no existing
  SignWell runner credential; no failing workflow was dispatched.
- Explicit Vercel project inspection matched
  `prj_LupoeEEcWigvtw6CII2bL46l0RB3`, HomeOfferFlow/dealdoc1s-projects.
- A fileless Development-environment subprocess reported the SignWell
  connection absent. No environment file was written or value displayed.
  Production Secrets were not retrieved, exported, copied or changed.
- Therefore actual API testing will reuse the existing authenticated owner-only
  server path rather than request a new credential or expose a production key.

## Fixed test and delivery behavior

`lib/listing_lead_signing_qa.py` builds seven actual source-backed pages and 42
fields across four fictional cases: unanswered/single Seller/Broker;
unanswered/two Sellers/Associate; explicit negative answers; and known facts
with Unicode continuation. The listing adapter's actual field geometry and
controls are retained. Only QA field IDs, combined page offsets and recipient
IDs are remapped: QA A represents Seller 1 and the professional; QA B represents
Seller 2. That sharing is test-only, not a change to customer recipients.

Four exact-one groups and four conditional rules exercise both positive and
negative completion branches. Source, renderer revision, page content streams,
fields, controls and case manifest are bound to reviewed layout digest:
`30f9711e64bff16ecbb44fb7031ed8e6f845afb0bf149629e84a13c65992e8e1`.
Changed printed content or geometry cannot reuse that review.
The reservation records that digest and a separate completion-controls digest;
read-only status rejects a foreign layout/source revision or signing order.

The existing reserved QA sender now supports an explicitly opted-in draft
verification step. Legacy purchase/showing/amendment behavior remains unchanged.
For this new test it:

1. Reserves the fixed QA attempt before creating anything at the provider.
2. Creates a test-mode private draft and saves its exact document identity.
3. Reads that draft and verifies identity, test mode, parallel invitations,
   metadata, every field/recipient/rectangle and completion controls.
4. Saves the verified pre-send state before the single send request.
5. Retains the same recorded attempt on rejection, missing controls, timeout or
   receipt failure; no duplicate test, automatic reminder or resend is possible.

The two new API actions accept only their action name, and require both the
existing platform-admin check and an existing approved owner email. They do not
accept a custom document, source, recipient, field map, test mode or revision.
The new collapsed owner-only admin section uses the existing control/transport;
its two new buttons have 44-pixel minimum touch targets.

API shapes were checked against the official
[Create Document](https://developers.signwell.com/reference/createdocument) and
[Update and Send Document](https://developers.signwell.com/reference/senddocument)
contracts. Supabase's current changelog/Data API guidance was checked; this work
reuses existing QA tables and server-side access, without schema or policy
changes. No new paid service or polling loop was introduced.

## Local verification

The final focused run passes **86 checks**, including the nine JavaScript
control cases exercised by its runtime wrapper:

```sh
python -m unittest tests.test_listing_lead_signing_qa tests.test_operator_listing_lead_signing_qa tests.test_operator_purchase_signing_qa tests.test_operator_showing_signing_qa tests.test_operator_amendment_signing_qa tests.test_signwell_controls tests.test_signwell_request_verification tests.test_signwell_delivery_adapter tests.test_signwell_delivery_coordinator tests.test_operator_signing_controls_runtime -q
```

Tests cover actual source-backed assembly, changed printed content/geometry,
fixed recipients/test mode, missing rules/checkbox constraints/text validation,
foreign metadata/recipient, failed checkpoints, send ambiguity, recorded-attempt
deduplication, read-only status, owner/admin checks and action-only routing.
All seven final placement-guide pages were visually reviewed, including source
X marks, dates/signatures, one/two-Seller initials, long Unicode and the 200-CJK-
character live text-box sample. They are **local simulated placement guides**,
not completed provider output.

An isolated actual-markup/controller preview verified check/send response
rendering and disabled duplicate-send controls on desktop and at 390×844.
Phone document width remained 390 pixels. CSP blocks external connections; the
fixture's fetch is a local simulation only. The temporary tab/server were closed
and viewport override reset. Evidence is outside Git in this chat's
`listing-lead-provider-qa-2026-10-17` folder: manifest, unsigned specimen, seven
page PNGs, and desktop/mobile owner-control screenshots.

Reproduce the specimen with
`python -m scripts.qa.listing_lead_provider_preview --output-dir <private-output>`;
this command cannot send. Reproduce the isolated UI with
`node scripts/qa/listing_lead_control_fixture.cjs <temporary-output>`.

## Next bounded workstream

Publish the fixed QA control through PR/green CI and one intentional production
release after checking live Vercel headroom. To avoid shipping unfinished listing
or disclosure work merely to run QA, isolate the QA-only patch on current main,
including its two small dependencies from `fcbf606`:
`lib/listing_lead_disclosure.py` and `lib/signwell_controls.py`, plus the existing
source asset's explicit API `includeFiles` entry. The new specimen/preview do
not depend on TXR-1101, private source registration, its migration or test-only
runtime imports. Do not include draft disclosure PR #1341.

Run the frozen QA-only full regression/CI once, publish, then use the actual
owner control and inspect the exact persisted draft/settings. If accepted,
complete its two fictional signers and review the final provider PDF. Respect
any action-time consent required by the provider; prior consent for another
packet is not authority to accept a new disclosure. Completion of this lead
specimen will not by itself prove completed-provider placement for the ten-page
TXR-1101 primary agreement or full listing-package orchestration.
