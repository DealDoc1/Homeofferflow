# Partner placement copy alignment

Date: 2026-10-22

## Contract

- The directory shows at most three partner profiles per category: the active
  Premier first, followed by up to two other partners.
- Guided transaction workflows and the offer-completion confirmation mention
  only the single top active Premier across HomeOfferFlow.
- Other Premier profiles, Featured Partners, and Core Partners remain in the
  directory only.
- Every tier remains complimentary during beta; no automatic paid conversion
  or future price is promised.

The shared API already applies `surface=directory` and `surface=workflow` to
enforce these limits. This slice aligns the public partner page, beta
application comparison, Texas partner guide, partner rate card, deployment
runbook, and contract tests with the implemented rule. The tests now
specifically guard against a return to the obsolete per-category workflow
wording.

## Verification

- Python: 123 focused checks across intake copy, public metadata, partner tier
  UI, offer completion, public partner selection, and public profile lookup.
  An additional 37 focused PWA shell checks passed. The full repository suite
  passed 2,940 tests with 23 skips, using the pinned test requirements in
  temporary storage. Partner selection and profile checks used in-memory
  fixtures; no network requests were made.
- JavaScript: 32 runtime checks across shared public partner profiles,
  offer-completion rendering, inspection workflow, and insurance workflow.
- JSON-LD parsing and the focused public metadata checks passed.
- Visual review: partner page at desktop 1280×900 and mobile 390×844; beta
  application comparison at desktop and mobile. The mobile table scrolls
  horizontally to the Premier column, while the page itself stays within
  390px. The comparison shows the three-profile cap and single-Premier
  workflow/completion rule.
- No partner application was submitted, no external write or message was
  made, no charge was incurred, and no deployment was attempted.

## Isolated production release candidate — October 22, 2026

This copy-only release candidate is based on the current production commit
`551d90644fb0cb0fa00492ea506a1736a09f6499`; its service-worker shell advances
from v126 to v127. Focused validation on the isolated candidate passes 146
Python tests and 32 JavaScript runtime cases. The complete Python regression
suite also completed successfully (exit 0). The partner page and Premier tier
were visually reviewed at 1280×900 and 390×844; at 390px the document
`scrollWidth` remains 390px and the Premier card clearly states the
cross-platform workflow and completion rule.

A read-only production Supabase query confirmed
`hof_partner_leads_partner_type_check` is validated and includes `title`,
`lender`, `inspection`, and `surveyor`, alongside the API-supported categories.
The API/database category contract therefore accepts title partners. No row was
read or changed. Vercel reports no connected Git project or origin connection;
automatic Git deployments remain off. This candidate remains **not deployed**;
no routine preview or partner submission was made.

**Implemented, tested, and visually reviewed locally; not deployed or
production-verified.** The repository has no `docs/CURRENT_PROJECT_STATE.md`;
the roadmap and release-evidence files are the available project records.
