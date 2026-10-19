# Seller-owned disclosure release candidate

## Scope and release authority

The owner has authorized roadmap implementation, GitHub push/merge, SQL and
intentional production release without another blanket approval. This release
makes the seller-owned disclosure questionnaire and corrected disclosure
rendering usable from the existing account/listing/offer entry points, including
individual sellers. It also fixes PDF access when embedded viewing is blank.
This is an incremental delivery of the active full roadmap, not its completion.

The release branch deliberately excludes unverified TXR-1101 sale-listing
renderer/interview, listing packet composer, listing-lead v2 mapping and their
two schema migrations. Those remain intact on `codex/listing-package-integrated`
and remain in progress. Purchase-offer combined disclosure inclusion is not
implemented by this release. Other prepared documents remain independent of a
missing or unfinished disclosure. Existing source/agent access and pricing do
not change. Automatic Git deployments remain false in vercel.json.

## Approved source and authorization

The supplied TREC-55-1 and optional TREC-61-0 sources are already approved in
the existing private source vault, revision 05-04-2026; no new source-owner
authorization is required. Main source SHA256:
`65a52e167c290814930624ba230e232c152573359f1388cdb5e1237a62e4239a`.
Water source SHA256:
`91056ab6520af8cbef319986e03490f1bf6947817c3d3f563348f80f957f871f`.
Current official and supplied full-page renders are equivalent. No source hash
or provenance check is weakened. Form use attestation and the private source
audit remain intact; neither introduces a brokerage-seat requirement.

Changed mapping scopes are `lib/trec_seller_disclosure.py` and
`lib/trec_seller_disclosure_schema.py` (TREC seller disclosure / TREC seller
disclosure schema), plus lossless written explanations and Unknown handling.

## Signing plan and rendered signed-PDF QA

Existing v4 provider document `b4ea4029-7e80-460c-880c-9e7275cee423` is confirmed
complete for both approved QA inboxes by message `1a1549e4544ba4f0` at
2026-10-19T14:43:36Z. Completed PDF SHA256:
`3ba4969659936ce930501bfba2434f6870cab0ecd472b3cd8cbc2defedb45829`.
All 13 comparison pages were rendered and visually reviewed: sole Seller,
four-party main/water execution, Unicode continuation and explicit Unknown.
The corrected date/signature regions and continuation initials pass this exact
completed signature visual QA. Renderer pins are unchanged and pass validation.

The confusing multi-case artifact is a technical specimen, not a client packet.
One normal four-page source/API output (six only when water is selected) was
separately reviewed; saved answers survive browser download without repeated
execution pages or a test watermark. This is an unsigned fictional example.

Signing uses current saved seller names/emails, parallel invitations, one PDF
and current per-seller review evidence. Public questionnaire send cannot add
buyers or substitute recipients. Buyer acknowledgment stays owner-authenticated.
Authenticated QA: ownership, email-session lifetime, revocation, saved-answer
integrity and review-version boundaries pass focused tests and actual isolated
PostgreSQL. Canonical authenticated acceptance remains a post-deploy check and
is not falsely claimed from the fictional browser fixture.

## Regression and schema coordination

Focused release checks: 75 passed in 0.482s, including exact renderer pin,
questionnaire/signing boundaries, normal source rendering, PWA and readiness.
Actual isolated PostgreSQL: 52 assertions passed against both exact migrations;
cluster exited after the test. No production schema changed during that run.
The frozen release must pass the full regression and golden checks in its
exact-head pull-request CI before merge. The existing intentional production
workflow also runs its required full regression; no extra local full rerun.

Apply only these pending migrations in order immediately before the coordinated
code deployment, then independently verify v2 readiness, private grants and RLS:

- `20261015164510_seller_disclosure_review_revision_binding.sql`
- `20261018134817_seller_disclosure_questionnaire_access.sql`

The previously unapplied questionnaire migration is scoped to currently
released form codes, not excluded TXR-1101. Deployment readiness now requires
the v2 contract and zero-row disclosure column probes, without customer reads.
No customer permissions are widened. Legacy unversioned reviews must be
reissued before they can authorize new content; existing signed packets and
historical review evidence are retained.

## Production target, cost and verification boundary

Baseline: main `61e516d0a091646bbff14a00624051d4e328d4fc`,
deployment `dpl_2agZyywm1ahG4Pk5tjdaWdZ3YfVx`, shell v106.
Candidate shell v107 includes only real existing release assets. Target remains
project `prj_LupoeEEcWigvtw6CII2bL46l0RB3`, team
`team_BZUBDsoLMwlnaXtIES35YT4S`, canonical www.homeofferflow.com production.

Use the existing read-only capacity check and its credit reserve before the
single intentional prebuilt release. No paid upgrade, routine preview, customer
packet or new multi-case invitation is authorized by this evidence file.
Verify canonical shell, API and normal seller flow afterward; record the actual
deployment identity and any incomplete acceptance separately. A green workflow
alone is not a full seller-suite or revenue-impact claim.

## Release coordination continuation

PR #1348 merged as `aedca42589c45c81e67ef4ac0a69c36b334e84a2` after exact-head
CI `39288563117`: 2,755 tests passed (three environment skips), approved golden
PDFs and signer geometry passed. Read-only capacity `39288255024` reported
$0.05 used / $19.95 unconsumed / $3 reserve. No production deployment started.

The review-revision migration applied successfully. The questionnaire migration
tool returned an expired-request error twice; independent database readback
confirmed its column/function absent and the original v1 readiness intact.
Do not blindly rerun the already applied first migration.

The still-unapplied second migration is now fully additive: retain the legacy
pending-link index, add the questionnaire-specific index, and add a private
`hof_seller_disclosure_schema_readiness` wrapper that delegates to the unchanged
core readiness RPC. The deployment checker calls that v2 wrapper. No DROP or
replacement of the legacy function is needed. Existing pending uniqueness,
review proof insertion and reissue semantics remain supported. Thirty-six
focused checks and 55 actual isolated PostgreSQL assertions pass, including
retained baseline/index, service-only wrapper access and questionnaire races.
This small follow-up must pass its own CI before deployment; it does not change
the reviewed renderer, customer UI or provider signing geometry.
