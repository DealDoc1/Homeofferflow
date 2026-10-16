# Completed disclosure provider QA exposed date overflow

## Evidence and result

The October 16 continuation inspected current production schema and test
inventory read-only. There were zero disclosure drafts/provider-linked drafts
and no disclosure QA scenario/run. SignWell's disclosure search found none,
and the corresponding invitation search was empty. Normal existing Google
sign-in restored the provider account; no credential or account setting changed.

Prepared one fictional compact test from the exact supplied TREC-55-1/61-0
sources and the 8cccf2b renderer. Thirteen execution/initials/continuation pages
cover one Seller without Buyers, four parties with water, Unicode overflow and
Unknown answers. Source content, field types/rectangles and required flags were
preserved; only composite page numbers, API IDs and QA recipient IDs changed.

One exclusively reserved provider draft was created:
c560d5f0-1aed-4878-b3bb-89b4e56cdc4c. All 71 fields passed provider geometry,
type and recipient readback. Initial send returned 422; the same document was
still an unsent draft. One explicit, identity-checked recovery returned 201 /
Sent. No second document was created. The first recovery inspection refused
the provider's Created spelling; the QA runner now reuses the existing
production created/draft normalizer rather than weakening the identity check.
The original rejection reason was not retained, so it is not attributed to a
particular provider cause.

Both approved inboxes received this exact invitation. The owner explicitly
authorized the final electronic-signature disclosures for both QA signers.
The first signer completed 37 fields, the second 34. Both final confirmations
finished. Downloaded the actual 13-page provider PDF, marked NOT LEGALLY VALID
(TEST MODE), SHA256:
155b68c08b49d03a2a67a0a23f587c8ee3123f74a336cff07f71ae6c0051e096.

**Visual result: FAILED, not a placement pass.** Main four-party page 3 and
water execution page 5 have oversized date text. Right dates wrap a final digit
below the rule; left dates crowd the next signature. The provider preserved
the requested fields but rendered date text at approximately 14.071pt in the
26px-high boxes. Therefore coordinate readback alone did not prove legibility.
Single-Seller and Unicode continuation pages were also inspected; initial
placement on the continuation was clear. Review stopped at the discovered
execution defect, not a claim that every page passed.

## Local correction and verification boundary

The main/water execution maps now reserve separate signature/date regions.
Signatures retain their vertical positions and use 216px width. Dates use the
established 18px-high format, keeping the same bottom above the source rule;
main dates have 96px width and water dates 80px. Left/right date starts move to
320/660px and stay within the independently measured source bounds. Date format
is MM/DD/YYYY and signing date is autofilled/locked, matching existing TXR-1507
practice and removing repetitive date entry.

The render revision advances to seller-disclosure-date-fit-2026-10-16-v4.
Earlier Seller reviews and the failed v3 provider specimen cannot approve v4.
No answers, source artwork, party order, agent access or billing changed.

Forty focused tests passed in 0.089s, covering source geometry, dated-row
baselines, separated regions, field width/height/format, party counts/offsets,
render-version reviews, send boundaries and the fixed QA runner. Main and water
QA rectangles were rendered and inspected for ordinary four-party and
single-Seller execution pages. Those rectangles are not real signatures and
do not establish the corrected provider font result.

Final frozen local regression: 2,692 tests in 87.189s, OK, one environment skip,
process exit zero. Log: /private/tmp/hof-disclosure-date-fit-full-20261016.log.
The later Invalid fixture PDF diagnostic is an intentional negative-test
output. Patch whitespace passed. Independent CI for 8cccf2b passed before this
map correction; it does not prove the corrected candidate's hosted checks.

The new runner is offline by default, uses only the two approved test inboxes,
keeps both test-mode body/header enabled, creates a private draft first, checks
provider fields before send and journals before side effects. A receipt prevents
another create. Same-ID recovery requires an exact verified rejected draft and
is allowed once. Tests cover byte mismatch, duplicate reservations, timeouts,
field mismatch, already-sent refusal and explicit recovery. The next v4 case is
pinned to exact reviewed renderer hashes and a distinct QA revision, so it
cannot accidentally reuse the failed v3 attempt.

## Artifacts and external scope

- Failed test receipt, composite, manifest and completed PDF:
  /private/tmp/hof-disclosure-provider-20261016/output/pdf/.
- Corrected local rectangle specimens:
  /private/tmp/hof-disclosure-date-fit-20261016/.
- Thread screenshots: disclosure-provider-2026-10-16/ under persistent output.
- Used the existing API key through a 0600 temporary file, removed after every
  attempt; no key was created, reset, printed or committed.
- One nonbinding test to andrewchri@gmail.com and brewbqinfo@gmail.com; no
  customer packet, reminder, charge, hosted build, production SQL or deploy.
  SignWell test mode is documented as nonbinding and excluded from API billing:
  https://developers.signwell.com/reference/createdocument.
- Source schema still lacks the pending review-version columns; the existing
  migration and API must release together. This provider specimen is not an
  authenticated live Seller-review-to-send pass.

Not deployed. Corrected v4 completed-provider review and coordinated release /
authenticated canonical verification remain unfinished. The first provider
attempt is completed evidence of a defect, not permission to ship that defect.
