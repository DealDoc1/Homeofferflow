# Integrated agent sale-listing package - local checkpoint

## Bounded workstream

- Outcome: integrate the actual sale-listing interview, private draft API,
  saved IABS and seller lead disclosure into one packet on current production
  code, preserving the newly corrected lead-explanation layout.
- Scope: merge the prepared `codex/txr1101-sale-listing` work into a branch
  based on production plus the reviewed local v2 explanation correction.
- Baseline: main `61e516d0a091646bbff14a00624051d4e328d4fc`, successful production
  run `39130371738`, freshly read before integration.
- Cost: no new invitation, real customer write, preview or deployment. Focused
  tests only; do not repeat the full suite for an unfinished form release.
- Evidence: conflict-free current code, source-enabled API/composer tests,
  preserved owner QA controls, and local desktop/390px review without sending.

## Integration and actual defect corrected

The integration preserves the current read-only QA diagnostics, the v2 lead
line-height/answer-area correction and fixed source/layout pins. It retains
the listing packet's conditional-control fingerprint binding and all prior
customer signing controls. Current production code is not replaced by the
older branch. The prospective app shell is reserved as v107 with both listing
interview assets; production still serves v106.

A newly added combined test uses the real private TXR-1101 source and the
actual API, renderer and delivery coordinator with a fully isolated fake HTTP
transport. It composes one 13-page file: 10 listing pages, one fictional saved
IABS, the real TREC 56-0 source and its corrected seller-detail page. IABS adds
no signature or initials. Lead fields/controls are offset and namespaced to
the correct pages and existing two Sellers/associate. Missing Seller's
Disclosure Notice stays visibly pending without blocking prepared documents.

This test exposed an actual retry-path defect: after the first successful
send, the identical retry returned 403 "unavailable or already sent." The
standalone send lookup now also reads the same owner's tracked sent/signed/void
record, requiring an exact durable document ID and fingerprint before entering
the existing delivery coordinator. The coordinator still verifies the entire
current reviewed request and provider identity. Unchanged requests reconcile
the existing document; they do not create or POST another provider send.
Missing/mismatched tracking, wrong owners and changed packet contents remain
rejected. Draft editing and checkpoint write scopes remain draft/failed only;
signed/void states are not overwritten. No roles or access permissions change.

The actual send dialog now reads the nested server delivery message rather
than claiming every successful retry sent a new invitation. Runtime coverage
checks sent, already-signed and ended-request messages plus legacy fallback.
The listing interview's unconfirmed-answer choice uses "Seller will complete
while signing" instead of exposing the signing-provider implementation.

## Verification observed

- Initial source-enabled integration: 223 focused Python checks, no skips.
- Final affected integration run: **291 checks passed, no skips**, 15.219 sec,
  including the real source, API/composer/lead adapter, legacy signing paths,
  durable delivery, recipient ownership, schema contracts and PWA controls.
  Node runtime matrices execute through those Python wrappers; do not add
  their case counts again. Log: `/private/tmp/hof-listing-integrated-final-20261018.log`.
- A narrower retry run passed 121 checks after correcting two new test-fixture
  assumptions: the real route nests its result under `signwell`, and real
  persisted rows always carry a status. The original failing retry was not
  dismissed or changed to expect the broken 403.
- Supabase static preflight: 119 local migrations, zero errors. The listing
  migration is **not applied** to production; this is not live SQL verification.
- Actual source-page/signature/choice geometry remains covered by the prior
  focused v2 text checkpoint. No new PDF layout is authored in this integration.
- Local fixture uses the actual merged send-dialog code with fictional data,
  simulated API responses and a CSP blocking external connections. Desktop and
  390x844 review show the 13-page contents, pending disclosure and enabled send;
  phone document width equals viewport width (390px). No send was clicked.
  Captures: chat output `listing-package-integration-2026-10-18/desktop-review.png`
  and `mobile-review.png`. These are local component checks, not live agent flow.
- Patch whitespace and merge-marker checks are clean. No production source
  registration, SQL mutation, provider send, billing change or new credential.

## Remaining release work

This is a backed-up integrated candidate, **not a customer release**. The
corrected v2 lead font/wrapping still requires actual provider confirmation
and completed-PDF review. TXR-1101 also needs its actual completed-provider
matrix, source registration and coordinated schema/API release. Seller's
Disclosure Notice integration stays separate from unfinished draft PR #1341;
the water-rights adapter is not implemented. Missing documents may remain
pending and do not stop the prepared listing package.

The safe standalone retry correction can be isolated and released against
current production without shipping these unfinished form/PDF changes. Do
not activate the entire listing candidate merely to deploy that correction,
and do not label local provider transport fixtures as completed signature QA.
