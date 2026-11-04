# Align protected QA transport with the API contract — November 4, 2026

## Evidence and bounded change

The v1 buyer-package create returned HTTP 400 with no confirmed document ID.
Its body was discarded; a read-only connection check succeeds. Its reservation
remains intact. No response field or exact root cause is established. Local
payload review against the official SDK's request models found no obvious
primitive-type mismatch; this was a source review, not execution of its
Pydantic validator or proof that every provider business rule passes.

The official Python SDK at commit
7d6811135600b4426b22904d5432ff1f2f39e0ed uses canonical POST paths without
trailing slashes and explicit application/json request/response headers:
https://github.com/Bidsketch/signwell-sdk-python/blob/7d6811135600b4426b22904d5432ff1f2f39e0ed/signwell_sdk/api/document_api.py.
The inspected reference checkout is private temporary research material, not a
dependency and not installed/executed. The current source contract also documents
X-TestMode-Enabled: true for both create and send:
https://developers.signwell.com/reference/createdocument and
https://developers.signwell.com/reference/senddocument. Send docs explicitly
warn that draft test mode does not automatically carry over to sending.

Added a QA-only transport helper using those canonical paths and JSON headers.
It requires an exact Boolean test_mode true before any provider POST and sets
the explicit true test-mode header on both create and send. It validates the
reserved send UUID and disables redirects per request even if a future client
allows them. It has no retries, configurable destination, logging, credential
lookup or journal writes. The coordinator rejects live/malformed test mode
before reserving an attempt and retains its existing reservation/readback/
checkpoint-before-send sequencing. The existing local sanitized rejection
capture will preserve bounded diagnostics for future necessary rejections.

Customer delivery adapters, shared customer readback guard, PDF renderers,
fields, sources, recipients, invitation order and API response shape are
unchanged. The fixed buyer recipe is now v2 with a distinct QA title/transport
metadata, so it cannot silently replay/reset the failed v1 reservation. It
remains a private test draft with the two established owner QA inboxes, parallel
invitations and no reminders. No automatic test send occurs on release.

Canonical transport alignment is a compatibility correction and a controlled
hypothesis for the rejected request, not a proven explanation of HTTP 400.
Do not claim that optional empty control arrays are invalid: the inspected SDK
models accept lists without a nonempty constraint, and those arrays remain
unchanged. Do not infer an undocumented request-size limit from the status.

## Verification and state

83 unique focused cases pass across signwell_qa_transport,
operator_qa_create_rejections, operator_purchase_signing_qa,
operator_showing_signing_qa, operator_amendment_signing_qa,
operator_listing_lead_signing_qa, listing_package_signing_qa,
lease_listing_signing_qa, buyer_representation_signing_qa and
signwell_qa_readback. Main run: 82 tests, no skips; the additional actual-packet
serialization case passed in the eight-case transport suite. Private buyer,
listing and lease sources were supplied. Existing HTTPX MockTransport inspects
actual serialized requests with zero network calls and no new dependency.

Coverage verifies exact canonical URLs, JSON headers/body, unchanged inputs,
explicit test mode on both requests, invalid/live mode refusal before writes,
invalid connection/document refusal without leaking a key, redirect refusal,
one-call rejection behavior, and existing coordinator lifecycle controls.
The actual nine-page PDF survives base64/JSON serialization byte-for-byte with
the same reviewed packet and field pins; it is not flattened or re-authored.
No changed PDF pages need rendering. Existing owner-control interaction and
locally authored nonbinding message were reviewed; no browser UI changed.

Implemented/tested locally. Source-approved packet and exact reviewed maps are
unchanged. No provider call, new packet, invitation, customer/partner message,
schema change, credential export, installation, charge or deployment occurred
during this preparation. A release candidate must pass its focused/full/CI/
live project/schema/cost gates before a single intentional prebuilt release.
Only then may one necessary v2 controlled test verify compatibility. The v1
attempt stays untouched, and completed-provider placement remains unproven.

## Frozen candidate checkpoint

The isolated candidate passes 99 focused tests with actual private sources,
including its QA-only customer-activation boundary and UI/control/classifier
regressions. Full local regression passed 3,011 tests, two skipped, in 120.846
seconds. No PR, deployment or v2 provider request has occurred. Work is preserved
on codex/buyer-qa-canonical-json-2026-11-04 while the owner prioritizes the live
My Offers search-focus defect.
