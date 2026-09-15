# Hydrostatic-testing authorization — local implementation foundation

## Roadmap finding

The live roadmap still described this workflow as unsupported and awaiting the
current official form. The current TREC forms page directly supplies TREC 48-1:

- Form page: https://www.trec.texas.gov/forms/addendum-authorizing-hydrostatic-testing-0
- Official PDF: https://www.trec.texas.gov/sites/default/files/pdf-forms/48-1.pdf
- Source revision printed on form: 11-19-19; listed effective date: March 1, 2020.
- SHA-256: `3eb6e7ced0723ceaab6bef2645fcd7868ee3c2cd2734a6a5f03dbe049bd5df6a`.

The source-file dependency is therefore resolved locally. This is not a claim
that the user-facing hydrostatic workflow is finished or deployed.

## Implemented and inspected

- Preserved the exact official source in `hydrostatic_testing_48-1.pdf`.
- Added `lib/trec_48_1.py`, filling canonical AcroForm fields and appearances without
  flattening the editable unsigned form or rewriting the form's legal text.
- Explicit choice among the form's three allocations of risk; no default selection.
  A capped-buyer selection requires a valid monetary amount. Switching to an
  uncapped choice clears the irrelevant prior cap. Addresses are not truncated.
- Verified all nine canonical field references are the same objects as the page
  widgets; no orphan recovery or duplicate-field insertion was necessary.
- Four possible signature positions are derived from the official signature-widget
  rectangles. Party IDs reserve 1/2 for Buyers and 3/4 for Sellers. No signature-date
  fields were invented on this form, which has none printed.
- Three complete one-page renderings (Seller, Buyer, capped Buyer) were visually
  inspected. Address, selected checkbox and capped amount were legible and aligned;
  unrelated fields and the legal text remained unchanged.
- Poppler initially reported an unwritable/default fontconfig cache. Rendering was
  repeated with a task-specific writable font cache, and the resulting capped-Buyer
  specimen was visually rechecked.

## Tests and boundaries

Eight new tests cover all risk selections, canonical and widget values, checkbox
appearance states, stale cap removal, malformed input, source integrity, four party
count combinations, and provider-coordinate bounds. Full suite: **1,981 passed**.

No customer data, signature, provider request, paid service, deployment, or Vercel
build was used. The review PDFs are synthetic unsigned QA intermediates kept outside
the repository. This is not completed-SignWell visual evidence.

## Required next implementation work

Connect the optional hydrostatic question and conditional risk/cap questions to the
existing purchase interview, reuse its address and party details, and append this
form to the single combined offer packet. Connect Seller recipients, absolute-page
signature fields, source/render fingerprinting, and the review summary. Verify
combined-packet ordering with other addenda and uploaded documents. Then run the
applicable completed-provider signing matrix under the existing release/cost policy.

Do not represent this module as a separate finished customer workflow or mark the
roadmap item production-ready. The existing production unsupported-path handling
has not yet been changed.
