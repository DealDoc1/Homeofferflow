# Receipt precision hotfix release candidate — November 2, 2026

## Exact scope

Base: verified production and GitHub main
`d150f6ac8e92af6e1c21e351b143f89e2c057833`, runtime
`dpl_6shLTAaiK9Rsy6R2hYkY7ka7RA9k`.

The only product-code change is `lib/email_delivery_store.py`. The receipt
acceptance PATCH retains exact key/fingerprint scope and pending status, but
uses the existing immutable, non-null attempt rather than equality against
a rounded JSON float. Invalid/unattempted timestamps cannot issue a PATCH.
The original timestamp, retry window, payload identity, and provider identity
remain unchanged. This is the same adapter fix checkpointed locally in
`76bff811`, isolated from the roadmap's unreleased form work.

Also included: its focused regression tests, the isolated database QA runner,
the runner's documentation, and this release evidence. No packet/form source,
PDF, renderer, field mapping, recipient routing, authentication, subscription,
Stripe behavior, API route, UI, workflow file, or migration is changed. Normal
automated regression and the existing schema guard are therefore applicable;
no new completed-provider signing specimen is needed for this code-only slice.
The local print/signing-diagnostic features are not part of this candidate.

## Verified cause and schema contract

Production logs showed Resend HTTP 200 followed by a receipt PATCH HTTP 200
and a still-pending read. Read-only SQL proved the stored float8 attempt did
not equal its reduced-precision output decimal. The enabled production
`hof_preserve_email_delivery` trigger makes key, fingerprint, creation time,
and the first non-null attempt immutable; accepted identity is final.
No production data was modified or email resent during investigation.

## Validation

- Full suite with the existing pinned `txr1101-runtime` environment:
  **2,946 tests completed successfully; 23 skipped**, 94.166 seconds.
  Versions verified: pypdf 4.3.1, reportlab 4.4.9, httpx 0.27.0,
  pdfplumber 0.11.9. The initial bundled-interpreter run used unpinned pypdf
  6.10.0 and lacked inherited child-process dependencies; its failures were
  resolved by using the existing correct environment, without test exemptions
  or product changes. No dependencies were installed locally.
- 69 focused email adapter/protocol/recovery/checkout tests and 15 customer
  summary runtime tests passed on the original local slice.
- 30 isolated PostgreSQL checks passed with the existing pinned runtime.
  They reproduce float serialization mismatch, verify corrected receipt
  acceptance, and retain immutable attempts, terminal identity, grants, and
  RLS. The private Unix-socket cluster had no TCP listener and was stopped.
- Supabase branch preflight passed (123 ordered migration files); no migration
  is added or applied. Whitespace checks passed.
- No customer-facing layout changes; accepted/unconfirmed summary states are
  covered by runtime tests. No customer packet or live send was used for QA.

## Release safeguards and authority

The owner requested the delivery incident fixed promptly and retains standing
authorization for verified, cost-checked releases. Use only the existing
confirmation-gated `production-release.yml` workflow, with the verified base
above, after the PR checks and committed-tree preflight pass. It repeats full
regression, target/schema verification, cost checks, a Linux prebuilt build,
one intentional production deployment, and canonical-domain smoke checks.
Do not deploy from this evidence alone before those checks pass.

Read-only November 2 checks: Vercel reports the intended project/team and
GitHub main matches production. Git auto-deployments remain disabled in
`vercel.json`. No deployments appeared in the checked recent window. The
authenticated Vercel current-cycle usage page shows Pro infrastructure usage
of $0.02 / $20.00 (Oct 22–Nov 22), above the required $3 reserve. Its data may
lag up to one hour; the release workflow must recheck headroom before building.
The plugin billing-charges endpoint returned 404, so no claim is made that it
passed. Existing GitHub release credential names were verified without reading
or changing their values. Public standard GitHub Actions runners are the
established release path; do not create a Vercel-hosted build or preview.

Rollback target: the existing READY production deployment above. No rollback,
deployment, customer email, signing request, credential change, charge, or
production data repair has occurred at the time this candidate was prepared.

## Remaining limits

This fix does not establish inbox delivery for the historical pending row.
That row has no retained provider ID or matching tagged webhook-ledger event;
receipt-only recovery still requires exact authenticated provider evidence.
Do not mark it delivered or resend it based solely on HTTP 200. SignWell's
separate HTTP 422 create rejection remains unresolved.
