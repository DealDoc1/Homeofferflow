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
  The local bundled Python runtime lacks `httpx`; these checks used a temporary
  import stub that raises on any real network call. All selected API tests
  replace the client with their in-memory fixtures. An additional 37 focused
  PWA shell checks passed using the bundled runtime.
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

**Implemented, tested, and visually reviewed locally; not deployed or
production-verified.** The repository has no `docs/CURRENT_PROJECT_STATE.md`;
the roadmap and release-evidence files are the available project records.
