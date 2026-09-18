# Loan-assumption purchase packet foundation - September 18, 2026

## Status and next work

**Local backend foundation; not a completed customer workflow, not deployed.**
The purchase interview has not yet gained its loan-assumption option. Browser
interview/restoration/review validation, completed SignWell output, and live
private-source retrieval remain unverified. The existing standalone interview
is unchanged. No push, deployment, external send, customer change, or new paid
resource occurred.

Next: connect these terms to the main price/financing interview, reuse seller
contacts, restore and clear conditional answers, update financing summaries
and estimates, and verify UI-to-PDF behavior. Do not present loan assumption
as generally available in the combined purchase path until that work is done.
Mixed new-lender/seller financing with assumed loans is not implemented by
this change; loan-assumption-only financing can include one or both existing
liens plus the cash balance. A contradictory legacy loanAssumption flag with
another financing type is rejected instead of silently issuing a cash packet.

## Implemented

- Validates source-form credit-document selections/deadline, first/second
  liens, lender names, balances/payments, fee/rate limits, variance election
  and threshold. Collects terms only: no credit judgment or lender request.
- Derives total assumed financing from selected balances using Decimal.
  Normalizes the offer's financing, loan amount, and cash portion before
  persistence/delivery identity generation; stale new-loan values do not win.
- TREC 20-19 Paragraph 3 now renders assumption financing amounts with exact
  cents and checks the assumption box, not Third Party Financing. Paragraph
  22 selects Loan Assumption. No Third Party Financing Addendum is appended
  for this path. Existing cash/conventional/FHA/VA/USDA behavior is unchanged.
- Private TXR-1919 is added to the same packet after the other generated
  purchase addenda and before uploaded documents. Uses real page counts for
  every signature/initial, including long-answer continuations. Canonical
  buyer IDs 1/2 and seller IDs 3/4 are maintained in all documents.
- Provider payload prepares one combined file with simultaneous invitations.
  Its message distinguishes signing the addendum from obtaining lender
  consent or releasing seller liability. No provider request was executed.
- Existing approved private-source lookup selects TXR-1919 server-side. No
  brokerage seat filter, new source approval UI, database migration, RLS,
  storage policy, auth, or subscription change was introduced. Supabase skill
  security review retained server-only credentials and private source bytes.

## Source and visual evidence

Private TXR-1919 / TREC 41-3 source, 11-07-2022, two static US Letter pages,
no canonical fields or widgets. SHA-256:
`048dfe44ddd32b2106fbc07189f410ba554defb30ba6ab072ac420eddb10b27f`.

The existing corrected TXR-1919 renderer/signing map is reused without changing
its coordinates or approved reference baselines. PDF skill checks rendered:

- Main contract pages 1 and 9 for both assumed loans: cash 230,000.20 plus
  assumed balances 270,000.35 equals price 500,000.55; both assumption X marks
  fit their source cells; unrelated financing boxes remain clear.
- Both addendum pages with two buyers/two sellers: amounts and choices fit
  the measured blanks; signature and initial outlines remain on their lines.
- Second-lien-only packet with long lender name: first-lien fields are blank,
  the lender name is preserved on a labeled continuation, and the buyer and
  seller each receive continuation initials. Main packet has 15 pages rather
  than the standard 14. This is unsigned field-outline evidence, not actual
  SignWell artwork or completed-signature QA.

`scripts/qa/assumption_packet_preview.py` reproduces the two synthetic cases
using an operator-supplied private source, with no network calls. Four private
PDFs are under `tmp/pdfs/assumption-packet/`, not Git. No client agreement or
signature was copied into a specimen.

## Tests

- 46 focused test methods passed: assumption packet, existing controlled
  launch cases, environmental integration, TXR-1919 renderer/source bounds.
- New coverage: exact cents, source-cell bounds, all buyer/seller counts,
  first/second-only selections, zero caps, malformed input, wrong source,
  deselection/stale answers, all-addenda/upload offsets, continuations, and
  mocked private-source/simultaneous-signing requests.
- Final full discovery: **2,162 tests; 2,160 passed; the same two approved-map
  comparisons failed**, 39.873 seconds.
  Log: `/private/tmp/hof-assumption-packet-suite.log`. The reference files were
  not updated to erase known placement drift.

No live Supabase query or completed-provider result is implied by mocked
request assertions. No browser result is claimed for an interview that has
not yet been wired to this foundation.
