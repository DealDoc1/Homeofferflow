# Purchase-contract disclosure and special-provisions preservation

## Status

Local implementation and unsigned visual QA only. Not pushed, deployed, or
verified through a completed SignWell packet. This work does not alter the
owner's executed client agreement or resolve the separate TXR-1507 incident.

## Confirmed defects

Both page-six fields in the TREC 20-19 renderer used character-count wrapping
limited to three lines. Replaying that helper with the synthetic long answer
returned three lines and omitted the final item for both brokerDisclosure and
specialProvisions. It provided no continuation or indication of omitted text.

The source has three differently sized blanks per section, not three equal
lines. Paragraph 8 begins with a narrow underscore blank at x=481.70..558.00,
followed by two blanks at x=61.34..557.38. Paragraph 11 begins at
x=349.20..554.40, then x=59.88..554.40 twice. The old special-provisions
starting x=45 was outside the printed paragraph. The source was read only.

## Local correction

- Place text using measured widths at eight points, on the printed blanks.
  If a word cannot fit the narrow first blank, it can use the next full line.
- If any entered text cannot fit, print "See continuation." and copy the
  complete answer under its Paragraph 8 or Paragraph 11 heading on a purchase
  contract continuation. Do not summarize, draft, or add terms.
- Preserve the existing specialProvisionsText alias and primary-value
  precedence. Render literal markup as text rather than executable formatting.
- Append after existing repair/non-realty/temporary-lease continuations but
  before adapter-added forms and uploads. Existing signature coordinates stay
  unchanged; buyer initials cover each added page. Only already-existing
  seller recipients receive additional initials; no seller is newly invited.
- Count lease continuation pages once when building the field map, avoiding
  repeated PDF generation for each new contract continuation page.

## Verification

- Nine new tests cover short/no-answer packets, independent source bounds,
  each overflow field, both fields across multiple pages, alias precedence,
  literal markup and long tokens, combined continuation ordering, unchanged
  existing signature fields, seller-recipient preservation, and upload page
  ownership. Initial focused run: 11 tests including source synchronization,
  all passing.
- After the page-count reuse optimization, all 57 combined repair,
  non-realty, lease, contract-continuation, and source-sync checks pass
  in 16.782 seconds. The full run below preceded only that optimization.
- Full discovery: 2,098 tests in 44.399 seconds; 2,096 pass and the same two
  TXR-1507 approved-map baseline checks fail. Those baselines were not changed.
  This is not an all-green release result.
- Three unsigned synthetic packets produced by
  scripts/qa/contract_terms_preview.py. Under the PDF skill workflow, visually
  inspected all six relevant rendered pages: page six in the short, wrapped,
  and overflow cases, plus all three continuation pages. Text clears labels
  and rules; the complete final item appears in both sections. No customer
  information or real signatures were used in these previews.

No production data changes, emails, provider API calls, Git publication,
Vercel usage, or paid resources. Actual completed-provider initials placement
and broader font/Unicode support remain unverified. Record this as local work
in the next daily report, not a deployed enhancement or measured revenue gain.
