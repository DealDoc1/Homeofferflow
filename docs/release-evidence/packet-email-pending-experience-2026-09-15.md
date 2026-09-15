# Packet ready, document email unconfirmed

## Implemented locally, not deployed

The subscriber generation route previously converted an uncertain document
email into a generic generation failure after PDF rendering, saved-offer
preparation, and the signing-request step had already completed. That response
lost the signing status and encouraged the customer to generate again.

The route now returns a structured packet-ready result with the existing offer
ID and signing outcome. An authenticated subscriber receives HTTP 202 when the
document email remains unconfirmed. Verified paid-checkout callbacks retain
HTTP 503 so their existing retry mechanism can resume the original immutable
email request. Invalid authentication still returns 401 before fulfillment.
Identity-validation failures are not converted into packet-ready responses.

The subscriber UI preserves the returned signing status, records the generated
packet rather than a false generation failure, and shows email uncertainty
separately. It retains the local draft while email is unconfirmed and offers
an account-workflow shortcut to the existing My Offers tab. Provider acceptance
is described as requested delivery, not proof of inbox arrival. Uncertain
signing does not claim that no invitation was sent or immediately urge another.
The static fallback heading no longer claims payment success.

## Verification

- Full local Python/Node suite: **1,921 tests pass**; `git diff --check` passes.
- Real HTTP-handler tests with controlled provider/storage responses cover
  subscriber 202, paid callback 503 then successful replay, expired receipt
  without another send, and invalid authentication without status disclosure.
- The actual subscriber JavaScript function runs against controlled fetch and
  persistence boundaries: a partial result reaches the success page with the
  signing/document-email fields, records one usage event for the generated
  packet, and never enters the generation-failure branch. A true server error
  still enters recovery and records no usage.
- Actual summary/render functions verify honest copy, draft retention, both
  signing outcomes, and primary-button navigation for account/consumer paths.
- Isolated headless Chrome rendered the actual local status markup/styles and
  summary function at 390px and 1100px. Both screenshots were reviewed; no
  horizontal overflow or page-script errors. External requests were blocked,
  external fonts and the unrelated partner directory were excluded, and the
  browser was closed. This is panel QA, not authenticated full-site QA.

## Remaining and release boundaries

No production email, SignWell packet, customer record, schema, or Vercel
deployment was changed. The durable-email schema and entire integration batch
must be released together after the existing publishing/cost holds are resolved.
Production verification remains outstanding. The 202 response does not promise
an autonomous retry worker; signed receipt reconciliation can confirm an
existing send, and legacy/no-event operational recovery remains separate.

The verification skill shaped the API-to-UI boundary tests; the browser skill
used the isolated Playwright fallback because agent-browser is unavailable.
No new paid dependency, background polling, or customer-facing technical jargon
was added.
