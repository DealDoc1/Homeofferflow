# Partner directory and Premier visibility

Date: 2026-10-22

## Contract

- The public provider directory displays no more than three partners in each
  category, ordered with the active Premier placement first.
- Buyer workflow recommendations and the offer-completion directory display
  only one active Premier partner per category. Featured and Core profiles stay
  available in the directory and do not appear in those workflow surfaces.
- Title, lender, inspection, and survey providers follow the same placement
  display rule. The copy asks customers to compare providers directly and
  confirm qualifications, availability, pricing, and terms.
- Beta profiles retain a clear “Beta partner” label together with the placement
  label. All partner links, portraits, approved public details, and aggregate
  click/impression tracking use the existing shared public-profile contract.
- The shared public API exposes additive `surface=directory` and
  `surface=workflow` query values. The directory view returns at most three
  profiles per category; the workflow view returns one Premier profile per
  category. Existing responses keep the `{ ok, partners }` shape, and callers
  without a view default to the restrictive workflow selection.
- The API selects eligible placements before reading opted-in profile details,
  keeping the workflow lookup small and excluding unused private lead records.

## Verification

Implemented locally in the public partner API, public directory, offer-
completion page, optional insurance and roofing workflow modules, and shared
partner-profile helper. Focused actual-source tests passed: 33 JavaScript tests
across directory, completion, inspection, and insurance surfaces; 49 Python
checks across API view routing/selection, directory, completion, and public-
profile behavior.
`git diff --check` passed. Runtime fixtures verify three directory profiles per
category, one Premier per category in workflow/completion, title inclusion,
public contact links, and existing analytics payload limits. The partner UI
fixtures confirm that view-specific lookups share their cache and retain the
existing labels and contact actions.

The public directory was also reviewed with fictional profiles at desktop and
390×844 mobile. Three profiles per category display with Premier first; the
partner tier, beta label, contact actions, filters, and category links wrap
without horizontal overflow. This is local UI evidence only.

**Not deployed or production-verified.** No production release or deployment was
attempted in this checkpoint.
