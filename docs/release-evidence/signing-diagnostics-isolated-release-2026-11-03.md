# Isolated signing-create diagnostics release — November 3, 2026

## Exact scope and outcome

Baseline: verified READY production `48c81d9abc1cc2b6d91caa96e93937fcb0daa47c`,
deployment `dpl_9xGNhgUVsmM3KyBihNHH3fJd5EhZ`. This release isolates only
`lib/offer_signwell_delivery.py`, new `lib/signwell_rejections.py`, diagnostic
and logging tests, and this evidence. The roadmap branch is preserved.

Rejected purchase-offer creates produce the fixed `signwell_create_rejected`
event with numeric HTTP status, a locally defined category and at most 16
allowlisted field paths. Flat and nested error shapes are supported with a
64-entry/visit traversal budget, depth/path allowlists and a 64-KiB byte-body
parse limit. Unknown keys collapse to known schema roots. No raw provider
message/value, name, email, URL, PDF content, header or credential is logged.
Customer error messages are locally authored, never provider text.

The adapter still creates only private drafts and raises the existing
DeliveryUnsent base class on rejection. No failed create proceeds to checkpoint,
inspection or invitation. Request body/headers, HTTP retry behavior, document
identity, source PDFs, renderers, signing maps, concurrent recipients,
readback checks, send endpoint, API response shape, interview, UI layout,
usage/billing, schema and workflow files are unchanged. The new subclass is
handled by the existing API error path. This candidate does not include the
roadmap's new API errorCode/UI behavior or required-field readback guard.
No shell update is needed for this server-only change.

## Tests and user experience

35 focused tests passed with the existing pinned txr1101-runtime environment:
`tests.test_signwell_rejections`, `tests.test_signwell_logging_hygiene`, and
`tests.test_purchase_offer_delivery_recovery`. They cover fixed categories,
flat/nested errors, hostile/private keys and values, malformed/large bodies,
output bounds, safe customer text and existing saved-request recovery.

The real adapter logging test supplies a mocked rejected private create with
private message/key/value content. It verifies the exact four-key safe event,
one draft create, zero database updates and zero follow-up provider reads or
sends. The old blanket prohibition on every print call was replaced by this
behavioral privacy test; raw-response-text and opt-in verbose-log checks remain.
No real network request is made by those tests.

The existing purchase API catches the same DeliveryUnsent base class. Source
and focused recovery tests verify failed-create errors remain unsuccessful,
without claiming an invitation or asking the provider to send a document.
Only locally authored failure explanations change; no layout or interview
change needs a fresh screenshot. Historical HTTP 422 cause remains unknown.
Full candidate regression passed: 2,968 tests, 23 skipped, 95.520 seconds.
Supabase branch preflight passed (123 migration files), whitespace checks pass,
and preflight reports no packet/form source or mapping change. Exact-head PR
CI remains required before merge/release.

## Release constraints

The owner retains standing authority for verified cost-checked product releases.
Use the existing production-release.yml after exact-head CI and local preflight.
Its live database, existing project and cost/reserve gates must pass before
building/deploying one prebuilt production artifact. Automatic Git deployments
remain disabled; do not create previews. No migration is required.

No signing request payload, provider rendering or successful signing behavior
changes, so the lean protocol does not require another completed-provider
signing specimen for this diagnostic-only change. This is not evidence clearing
other form/map QA or permission to reproduce a customer failure for logging.

No customer packet, email, invitation, production data write, credential change,
installation, charge or deployment occurred during candidate preparation.
The historic provider response was discarded; deployment enables future
required requests to yield safe diagnostic evidence, not retroactive recovery
or a claimed fix for the original rejection. Do not replay the client packet.
