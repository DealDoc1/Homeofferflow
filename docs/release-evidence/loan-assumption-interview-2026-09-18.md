# Loan-assumption purchase interview - September 18, 2026

## Status

Local interview and combined-packet candidate, not deployed. Extends the local
backend foundation in `900de626`. No customer document, email, provider send,
live database record, deployment, or paid service was changed. Completed
SignWell artwork and live private-source retrieval are still unverified.

## User experience

- Loan assumption is a financing choice beside the existing mortgage/cash
  choices, not a second document interview. It asks which existing liens are
  assumed, then only those lenders, balances, current payments, fee/rate caps,
  credit-document choices/deadline, and loan-balance variance terms.
- No loan, documentation, fee, rate, or variance election is preselected.
  The page explains that signing does not obtain lender consent or release
  the seller. No lender request or credit decision is made.
- Exact-cent balance and cash totals are derived from selected loans. Current
  payments are shown only when supplied; the new-mortgage payment estimator
  is hidden to avoid implying an assumed loan has new amortization terms or
  double-counting escrow. Cash is labeled before deposits/credits/closing costs.
- Seller contacts reuse the existing shared signing section. Both generation
  paths validate assumption terms and the packet's buyer/seller contacts.
- Hidden new-mortgage answers are excluded from an assumption submission but
  remain editable if the user changes back. Unselected assumed loans and other
  credit-document text are cleared from the submitted packet, not from the
  current editable form. Restoring a different draft clears old answers.
- Review includes each selected lien, balances/payments, caps, documentation,
  deadline, and variance terms. Text is escaped. The packet tag and signing
  summary identify loan assumption and simultaneous invitations.
- Appraisal choices and new-mortgage validation/defaults do not leak into this
  path. Existing new-mortgage requirements remain in effect for those loans.

## Verification

### Runtime and regression

The actual application helpers, collector, price-step validator, restoration,
calculator exclusion and review execute in 14 new JS runtime cases. They
cover exact cents, malformed amounts, both/one/no selected loans, zero caps,
missing seller email, inaccessible hidden terms, draft isolation, deselection,
escaped review, and preservation of editable new-mortgage amounts. Existing
number, checkout, delivery, and restore harnesses were updated for the new
dependency; no map baseline was changed. Those 147 related JS cases passed.

Focused Python run: 22 methods passed, including packet generation, subscriber
partial-delivery behavior, financing defaults, and the new runtime wrapper.
Final full discovery: **2,163 methods, 2,161 passed, the same two approved-map
comparisons failed**, 39.974 seconds. Log:
`/private/tmp/hof-assumption-interview-suite.log`. No approved baseline was
overwritten to make this result appear green.

### Browser to local PDF

Used the browser-verification skills. The agent-browser CLI was unavailable,
so the connected Chrome browser was used with one temporary tab, then closed.
The localhost-only bridge extracts the real price-step markup, financing
helpers, answer collector, shared seller fields, and validations. Its Python
bridge calls the real packet adapter with synthetic buyer/property data and
an operator-supplied private TXR-1919 source. This is not the entire authenticated
production application, persistence, payment, email, or SignWell flow.

Observed successful local results:

| Choice | Pages | Assumed balance | Cash portion | Signing fields |
| --- | --- | --- | --- | --- |
| Both liens | 14 | 270,000.35 | 230,000.20 | Initials p13, signatures p14 |
| Second lien only | 14 | 30,000.23 | 470,000.32 | Initials p13, signatures p14 |
| Switch to cash | 12 | No assumed loan | Existing cash behavior | No TXR-1919 fields |

Both assumption examples retain the exact 500,000.55 sales price from browser
input to server-rendered contract. Deselected first-lien fields were empty in
both the submitted answers and generated addendum. `providerContacted:false`
was returned in all three cases. No credentials were needed by the bridge.

PDF skill: rendered and visually inspected contract page 1 and both addendum
pages for the two assumption examples. Selected X marks, amounts, rates,
addresses, lender names and deadline were legible within their blanks. These
are unsigned documents; the returned signature map is not proof of actual
completed SignWell artwork. Private PDFs/images remain untracked in
`tmp/pdfs/assumption-browser/`.

Browser error log contained "Could not establish connection. Receiving end
does not exist." The functional local calls succeeded; no error-free browser
claim or definitive attribution of that message is made. Server was stopped.

## Remaining work and discovered issue

- Completed-provider placement and live private-source retrieval for this
  combined path remain unverified. No source or map approval was fabricated.
- Mixed new-loan/seller financing with assumed loans remains unsupported.
- **Next correction:** the existing `moneyNumber` helper and non-assumption
  renderer use whole-dollar rounding. Browser cash deselection reproduced
  500000.55 becoming 500001. This predates this change. Assumption now bypasses
  the helper for price and derives balances in integer cents, but other money
  fields/paths need a coordinated collector/calculator/PDF precision fix and
  regression tests. It is local work remaining, not an external blocker.
- The source-bound geometry baseline failures remain recorded separately;
  passing interview checks do not authorize publishing an unverified map.

No push or deployment. Existing release and cost restrictions remain in force.
