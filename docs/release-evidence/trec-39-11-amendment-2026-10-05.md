# TREC 39-11 Amendment to Contract release evidence

## Scope

HomeOfferFlow adds a concise, document-specific interview for amending an
already executed residential contract. An authenticated Texas agent selects
only the contract terms that need to change, reviews the prepared amendment,
and confirms one or two Buyers and one or two Sellers before sending parallel
signature invitations. No brokerage seat, broker signature, or professional
recipient is required.

## Official source

- Form: TREC 39-11, Amendment to Contract
- Revision printed on source: May 4, 2026
- Effective date: July 1, 2026
- Official URL: `https://www.trec.texas.gov/sites/default/files/pdf-forms/39-11.pdf`
- SHA-256: `d12909bcbd014080948eb6f9771231ba1b1d98c64eaf07e87ab0faa1118b8d36`
- Test-only exact-source fixture: `tests/fixtures/trec_39_11_source.pdf`
- Production secure-source row and private-object upload: pending release

The public TREC source is used as the exact rendering base. The production
application will continue to retrieve the source through the existing private
form-source vault; the fixture is excluded from Vercel because the `tests/`
tree is not deployed.

## Implemented behavior

- Adds “Amend an existing contract” to the authenticated purchase-document
  interview and account form library.
- Uses conditional questions for the ten printed amendment choices and hides
  irrelevant fields.
- Automatically calculates the amended sales price from cash plus financing.
- Rejects contradictory option-period extension and waiver choices.
- Keeps the broker's final-acceptance date blank.
- Preserves long repairs and other-modification text on paginated continuation
  pages with initials for every selected Buyer and Seller.
- Maps one or two Buyers and one or two Sellers to the printed signature lines.
- Sends all parties in parallel; no agent or broker is a signing recipient.
- Adds the source allowlist, database constraint migration, service-worker
  asset, render revision, signing-map revision, and aggregate admin metric.

## QA status

- Official source hash and printed revision: verified locally.
- Focused parser, renderer, source-gate, UI, offline-shell, and signing-path
  tests: 38 passed.
- Ordinary populated source PDF: visually reviewed; answer marks and text fit
  the printed blanks without clipping or overlap.
- Four-party long-text continuation: visually reviewed across three pages;
  text is lossless and all four initials lines remain clear.
- One-Buyer/one-Seller option-waiver variant: visually reviewed; only the
  selected waiver is marked and all unused blanks remain clear.
- Unicode continuation variant: visually reviewed; curly apostrophes,
  accented text, and the one-half character remain legible and complete.
- Local browser QA: the authenticated library card and concise interview
  render with no script warnings or errors. Conditional sales-price questions
  calculate `$500,000.00` from `$125,000.00` cash plus `$375,000.00`
  financing. Option extension disables waiver; clearing it re-enables waiver;
  selecting waiver disables extension.
- Completed SignWell test-mode PDF visual review: pending.
- Full repository regression suite: 2,463 tests passed in 78.531 seconds using
  the documented release environment.
- Supabase branch preflight: passed with 115 unique, ordered migrations.
- PR, CI, merge, migration, secure source activation, intentional production
  deployment, and canonical-domain verification: pending.

This document records a local release candidate. It does not claim that TREC
39-11 is live until the remaining provider, regression, and production gates
are completed.
