# Purchase offer with a seller-reviewed disclosure

## Release scope and decision

Candidate: `codex/purchase-disclosure-execution`, shell v112. Production baseline
is PR #1352 / afc44a9b, shell v110. This batch adds a seller-reviewed, unsigned
TREC-55-1 and optional TREC-61-0 to the existing TREC 20-19 purchase offer package.
Existing seller-signed PDF reuse is preserved. No customer TXR-1101 activation,
listing migration, native app, commercial change or real client send is bundled.
Release only the immutable commit that passes exact-head CI, with its one
coordinated additive migration. Canonical acceptance follows deployment; it is
not claimed from a local fixture.

## Approved source and authorization

Existing approved private sources, revision 05-04-2026, are unchanged:

- TREC-55-1 SHA256 `65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a`.
- TREC-61-0 SHA256 `91056ab6520af8cbef319986e03490f1bf6947817c3d3f563348f80f957f871f`.

The owner has authorized these sources and continuing implementation, SQL,
GitHub push/merge and intentional production deployment. No further source-owner,
brokerage-seat or per-agent approval is introduced. Sources remain in the private
source vault, fetched only server-side through existing approved-source records.
Form-use/agent attestation and source fingerprints remain intact. Existing
TREC-20-19 source/renderer pins and all published legal text are unchanged.

## Signing plan

Buyers retain IDs 1/2; Sellers retain IDs 3/4. Seller destinations come from the
current, exact seller-review evidence, not browser overrides. Reversed seller
order maps to existing offer identities. Signatures, locked dates and necessary
initials reuse the unchanged v4 disclosure maps. All included recipients receive
invitations concurrently, with no signing order. The Seller executes the
disclosure and the Buyer acknowledges receipt; adding this document does not
add a Seller purchase-contract acceptance signature. Existing other-document
roles remain unchanged; conflicting recipient identity is refused before send.

The version/recipient/source/field fingerprint and exact disclosure are bound
atomically at the existing saved-offer journal checkpoint. Retries retain the
same provider document and inclusion decision without another allowance charge
or document email. Missing or unfinished disclosure remains explicitly excluded
and separately completable; it does not block other ready purchase documents.

## Rendered signed-PDF QA

Reused exact component placement proof: completed SignWell disclosure document
`b4ea4029-7e80-460c-880c-9e7275cee423`, both approved QA signers complete;
SHA256 `3ba4969659936ce930501bfba2434f6870cab0ecd472b3cd8cbc2defedb45829`.
All 13 technical comparison pages were reviewed for one/multiple Sellers,
Buyer/Seller main/water execution, actual dates, initials, Unicode continuation
and Unknown handling. See `seller-disclosure-v4-completed-review-2026-10-19.md`.
That comparison specimen is not a client package and was not resent.

The unchanged purchase-contract component has its separately recorded completed
provider evidence in `purchase-provider-completion-2026-10-12.md`; no contract
rectangle is modified by this batch. New actual-source local compositions are
one ordinary 16-page purchase/disclosure package and one 19-page four-party,
water/Unicode package. Every appended page renders pixel-identically before and
after merge. Changed execution/continuation pages were visually reviewed with
placement guides. This is reused completed component proof plus new composition
proof, NOT a newly completed live combined purchase-signing roundtrip.

## Authenticated QA and regression

Real browser -> actual Python HTTP handler -> actual owner-scoped store -> source
renderer -> client response was exercised in a loopback-only fixture. Auth and
database/storage responses were fictional; no production permission or hosted
write was used. Reviewed selection, metadata-only dashboard save, PDF preview,
removal, existing signed-copy reuse and delayed-response rejection after account
change, draft change or Cancel passed. Bound disclosures do not offer a second
standalone send. Desktop 1280px and mobile 390px were inspected; mobile document
and scroll width are 390px, dialog width 358px. Final local screenshots are in
the chat output folder, not public repository assets. The temporary tab/server
were closed; the viewport override was reset.

Local full regression: 2,860 methods passed in 93.093 seconds, five environment
skips. Focused UI/PWA checks: 88 passed. Isolated real PostgreSQL: 111 assertions
passed, no TCP listener, cluster stopped in finally. This includes edit/send,
competing-offer and proof-retirement races, client-recipe forgery rejection,
listing association exclusion and nonblocking routine viewed timestamps. The
final timestamp-lock narrowing was checked by that actual database test; fresh
exact-head CI covers the complete frozen tree. Source-backed planner methods
also passed using actual approved PDFs with source validation unmocked.
Signer geometry matches the approved baseline; branch preflight has 121
migrations and no errors. Full CI additionally checks golden PDFs and whitespace.

## Coordinated schema and release authority

Apply only `20261020140935_bind_reviewed_disclosure_to_purchase.sql` with this
code release, after CI. It adds an offer FK/index and private invoker-only guards,
retains existing RLS/grants/readiness functions, and adds an independent private
readiness wrapper. The release checker requires it and zero-row column probes.
No listing migration is needed or applied. Verify the live baseline function
hashes and new private readiness after the migration, without reading customer
rows. Automatic Git deployments remain disabled. Use one intentional prebuilt
release and its built-in spend protection; no standalone usage query or preview.

Rollback: restore the previous production code while retaining the additive
association/history guards and existing signed packets; never delete bound
disclosure answers, review evidence or provider requests. Production verification
must check the canonical authenticated picker, current shell and no-send preview
using a clearly fictional owned draft, plus ordinary signed-copy and pending
behavior. Do not send real client packets or another QA invitation for a smoke
check. No measured revenue/conversion uplift or whole-roadmap completion is
claimed; expected UX benefit is less duplicate entry and manual PDF handling.

Detailed implementation and bounded test commands are recorded in
`purchase-disclosure-execution-2026-10-20.md`.
