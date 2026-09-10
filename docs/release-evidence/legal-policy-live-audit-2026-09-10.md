# Legal package live audit — September 10, 2026

## Scope

This is a production-readiness audit of the public legal package and the
versioned acceptance controls that protect checkout. It records what was
verified on September 10, 2026; it is not a substitute for legal advice or a
fresh end-to-end paid checkout test.

## Public pages verified live

The canonical production pages were fetched directly from
`https://homeofferflow.com` and each displayed the same current disclosure:

| Page | Live disclosure |
| --- | --- |
| `/terms.html` | Version 3.0 · Last updated: July 30, 2026 |
| `/privacy.html` | Version 3.0 · Last updated: July 30, 2026 |
| `/esign-consent.html` | Version 3.0 · Last updated: July 30, 2026 |
| `/disclaimer.html` | Version 3.0 · Last updated: July 30, 2026 |

The source pages in this release branch contain the same public version and
date, preventing a release from silently reverting the package.

## Acceptance and checkout controls reviewed

- The offer interview requires an explicit acknowledgement and records the
  immutable policy version `2026-07-30` in `hof_legal_acceptances`.
- OnDemand checkout records acceptance before creating its checkout session.
- Standard subscription checkout independently checks for current acceptance
  on the server and returns a 403 before contacting Stripe when it is absent.
- The database record is owner-scoped, versioned, and has no update policy;
  it therefore preserves the original acceptance event rather than allowing a
  browser user to rewrite it.

## Production data check

An aggregate-only production query found one current-version acceptance:

| Policy version | Source | Count |
| --- | --- | ---: |
| `2026-07-30` | `offer_wizard` | 1 |

No account identifiers, timestamps, or personal data were exported for this
audit.

## Remaining evidence boundary

This audit proves the live pages, version alignment, persistence, and
server-side guard. It does **not** claim that a fresh signed-in subscription
or OnDemand checkout was completed today. That test remains a separate,
controlled Stripe test-mode QA task and should be captured with its checkout
and webhook evidence before treating the full billing lifecycle as newly
re-verified.
