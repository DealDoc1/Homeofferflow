# Listing packet composition - October 17, 2026

## Bounded outcome and baseline

Agents should receive one actual document packet, not a checklist described as
attachments. This batch builds the reusable PDF/field composer, connects it to
the existing private listing preview and tracked signing path, and implements
the first related-document adapter: the actual login's saved IABS when selected.

Scope: `lib/listing_packet.py`, the listing preview/send and recipient-review
handlers, concise packet contents in the existing send dialog, and focused QA.
Production/main was read back as
`7b408eb09b46720261e8fed4712fe42e81547f33`; the local starting checkpoint was
`bbe944f2ef08aad895c0a53dabc20fba10230107`. Automatic Git deployments remain
disabled. **This is local implementation and verification, not a deployment.**

No new service, queue, database table, migration or dependency was introduced.
The existing stateless Python backend and private agent-document storage are
reused. No production SQL/storage write, provider invitation, email or billing
change was made. The GitHub main and separate disclosure PR reads were read-only.

## Implemented behavior

- The composer preserves all primary listing pages and answer continuations,
  then adds prepared related PDFs in the source Paragraph 19 order. It emits
  one PDF, one combined field group and a manifest of actual included page
  ranges. Selected documents not supplied by a verified adapter stay pending;
  they are not fake attachments and do not prevent sending prepared documents.
- Each related field explicitly maps its local recipient to an existing
  reviewed Seller/associate/broker. Field identifiers are namespaced and page
  offsets are calculated from actual PDF lengths, including continuations.
  Unknown signers, duplicate/unselected documents, duplicate identifiers,
  invalid field bounds, encrypted/malformed PDFs and incompatible mapped page
  geometry fail before an invitation. Information-only rotated pages are
  accepted because no new signing map is applied to them.
- Editable PDF fields are retained with per-document canonical namespaces.
  A cryptographically signed/certified original is not rewritten into a new
  signing packet. Ordinary provider-rendered signature content is not erased.
  Combined input bytes and total pages are bounded. Large-document hosting or
  streaming beyond the existing preview transport has not been implemented or
  production-tested by this batch.
- If A (IABS) is selected, the API reads `hof_agent_documents` only for the
  verified actor and `document_type=iabs`. It independently checks the returned
  owner, type, private bucket, MIME type and exact `<actor>/iabs.pdf` path before
  reading storage. It never follows arbitrary URLs, the source host's files,
  another login's document or the canonical professional-profile owner.
- The saved IABS is appended unchanged in content, without adding a signer,
  acknowledgement, signature or initials. The primary signer map is retained;
  its appended information page is not misclassified as a listing continuation.
  If no actual related PDF is added, the primary PDF bytes are returned intact.
- A missing metadata row or missing storage object leaves IABS pending and
  permits the listing to continue. A transport outage or invalid/wrong-owner
  file is a visible error, not a silent successful attachment or send.
- Recipient review reports actual included labels, page count and pending
  documents in a compact expandable "Your packet" section. No private storage
  paths or source hashes are exposed as customer-facing document names.
- An opaque content confirmation is returned with that review and sent by the
  actual dialog. It binds record/actor, source, overlay, professional identity,
  saved answers, prepared-document fingerprints and composed fields. A changed
  or removed IABS, changed printed identity or tampered/missing confirmation
  cannot silently change the packet between review and send. Reopening the
  existing dialog refreshes the review; no extra approval question is added.
- Existing durable delivery still verifies provider fields before invitations,
  retains simultaneous signing, and reuses the same provider record on retry.
  Variable PDF creation timestamps do not change a logical packet fingerprint;
  a changed IABS file does. Broker signing contacts are reviewed separately
  without invalidating the packet merely because a missing contact was entered.

## Verification

Focused source-enabled run: **98 Python checks passed, no skips**:

```sh
HOF_TXR1101_SOURCE=/path/to/private/TXR-1101-2026-06-15.pdf \
python -m unittest tests.test_listing_packet tests.test_txr1101_api \
  tests.test_standalone_recipient_preview tests.test_txr_1101 \
  tests.test_txr1101_interview_runtime tests.test_agent_iabs_profile -q
```

An additional **91 affected signing/schema/delivery checks passed**:

```sh
python -m unittest tests.test_signwell_delivery_coordinator \
  tests.test_signwell_delivery_adapter tests.test_txr_signing_request_path \
  tests.test_standalone_form_schema_contract \
  tests.test_standalone_agreement_schema_contract \
  tests.test_standalone_agreement_foundation -q
```

The actual queue/interview scripts passed 37 Node cases (three new packet
summary/escaping cases, eight private PDF viewer cases and 26 listing cases).
The Python wrappers include these runtime checks; do not add their case counts
to the Python total as if they were independent full-site runs. Syntax and
`git diff --check` checks passed. Expected simulated storage failure logging
appears in the API negative test; it is not a live-service failure.

API transport tests verify the actual merged file, no extra IABS signer/fields,
missing-document continuation, exact private path checks, safe unchanged retry,
changed-file rejection and fresh-review recovery. Generic B/C/P composition
tests use explicitly fictional component PDFs. **Those tests do not implement
or verify the real seller-disclosure, lead or water-rights adapters.**

### Browser and PDF review

The isolated fixture uses the actual send-dialog/queue code, a simulated API,
fictional parties and a CSP blocking external connections. At desktop and
390 x 844 phone size, included and pending labels were visible, send stayed
enabled with a pending seller disclosure, and page width stayed 390/390.
The simulated submit carried all three reviewed recipients plus the exact
64-character review confirmation. The fixture deliberately rejected delivery;
no provider/email request was possible. No warnings/errors were seen before
that deliberate negative send test.

Screenshots outside Git, relative to the persistent chat output root:
`txr1101-packet-ui-qa-2026-10-17/desktop-packet-summary.png` and
`mobile-packet-summary.png`. These show **local fictional QA**, not production.

`scripts/render_txr1101_packet_qa.py` generated ordinary two-Seller,
single-Unicode-Seller and two-Seller continuation specimens from exact source
SHA-256 `eeec91ef481059834262cf7f842afc045bf17c09b5be9e79fe2508112310b068`.
Their total lengths are 11, 11 and 13 pages. All six boundary images were
visually reviewed: the last primary/continuation page and appended information
page for each case. Primary signatures/dates/initials stayed on their source
rules; no fields appeared on the appended page. The added page is visibly
marked fictional and is not a real IABS. Artifacts remain outside Git in
`txr1101-packet-qa-2026-10-17/`. These placement guides are not completed
SignWell PDFs and do not prove live-provider placement.

## Remaining work - not owner-created blockers

Only the saved-IABS adapter is currently connected. Complete source-specific
seller-disclosure/lead/water/other related-document preparation and package
adapters; do not replace them with dummy pages or infer Seller facts. Keep
unfinished disclosure PR 1341 separate until its completed-provider date-fit
QA and coordinated migration are ready. Its remote head was read as
`c5b6ada2684a89b8216d73249d87f7aa15c982c2`, still open/draft work.

Private TXR-1101 source registration, coordinated allowlist/readiness migration,
live completed signing/PDF QA, shell bump, frozen full regression, exact-head
CI, fresh spend check and intentional production release also remain. This
batch does not make the entire listing package or TXR-1102 lease workflow
complete. No owner action is needed for continued local engineering work.
