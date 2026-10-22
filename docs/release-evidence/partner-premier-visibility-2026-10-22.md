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

## Verification

Implemented locally in the public directory, offer-completion page, optional
insurance and roofing workflow modules, and shared partner-profile helper.
Focused actual-source tests passed: 33 JavaScript tests across directory,
completion, inspection, and insurance surfaces; 29 Python checks across partner
directory, completion, and public-profile behavior. `git diff --check` passed.
Runtime fixtures verify three directory profiles per category, one Premier per
category in workflow/completion, title inclusion, public contact links, and
existing analytics payload limits.

**Not deployed or production-verified.** No production release or deployment was
attempted in this checkpoint.
