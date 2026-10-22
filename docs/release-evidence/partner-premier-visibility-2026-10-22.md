# Partner directory and Premier visibility

Date: 2026-10-22

## Contract

- The public provider directory displays no more than three partners in each
  category, ordered with the active Premier placement first.
- Buyer workflow recommendations and the offer-completion directory display
  only the single top active Premier partner across all categories. Featured
  and Core profiles stay available in the directory and do not appear in those
  workflow surfaces.
- If legacy data contains multiple active Premier placements across different
  categories, the shared API chooses one deterministically by category, partner
  name, and placement ID. Category-filtered workflow requests cannot promote a
  second Premier.
- Title, lender, inspection, and survey providers follow the same placement
  display rule. The copy asks customers to compare providers directly and
  confirm qualifications, availability, pricing, and terms.
- Beta profiles retain a clear “Beta partner” label together with the placement
  label. All partner links, portraits, approved public details, and aggregate
  click/impression tracking use the existing shared public-profile contract.
- Free-beta administration keeps each application's selected Core, Featured,
  or Premier preference and sets every tier's monthly fee to $0.
- The shared public API exposes additive `surface=directory` and
  `surface=workflow` query values. The directory view returns at most three
  profiles per category; the workflow view returns at most one Premier profile
  across categories. Category-filtered workflow requests apply the platform-wide
  selection before filtering its result. Existing responses keep the `{ ok,
  partners }` shape, and callers without a view default to the restrictive
  workflow selection.
- The API selects eligible placements before reading opted-in profile details,
  keeping the workflow lookup small and excluding unused private lead records.

## Verification

Implemented locally in the public partner API, public directory, offer-
completion page, optional insurance and roofing workflow modules, and shared
partner-profile helper. The cross-category selector, beta tier defaults, and
category-filter behavior passed 128 focused Python tests across partner
selection, beta onboarding, API routing, metadata, directory, and public-
profile behavior, plus 32 JavaScript tests across completion, inspection, and
insurance surfaces. The complete Python suite passed 2,938 tests.
`git diff --check` passed. Runtime fixtures verify three directory profiles per
category, one Premier across workflow/completion surfaces, title inclusion,
public contact links, and existing analytics payload limits. The partner UI
fixtures confirm that view-specific lookups share their cache and retain the
existing labels and contact actions.

The public directory was also reviewed with fictional profiles at desktop and
390×844 mobile. Three profiles per category display with Premier first; the
partner tier, beta label, contact actions, filters, and category links wrap
without horizontal overflow. This is local UI evidence only.

**Not deployed or production-verified.** A read-only production API check on
2026-10-22 showed that the deployed workflow endpoint still returned Core beta
profiles. This local branch now contains the restrictive cross-category
selector. No production release or deployment was attempted in this checkpoint.
