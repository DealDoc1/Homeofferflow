# TXR-1501 execution correction candidate — September 18, 2026

**Local candidate only. Not deployed, not completed-provider verified.**
Existing customer agreements and approved geometry references are unchanged.

## Source finding

Read and rendered page 6 of the privately supplied TXR-1501 06-15-26 source.
Source SHA-256: `d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd`.
Source remains private; no form or client artwork is committed.

The left signature rule spans PDF x=36..288.05 at top-origin y=443.22999..443.83.
Immediately below it are the broker and broker-associate role checkboxes. Both
roles use this same rule. The lower left rule at y=484.63002..485.23 is labeled
for the associate's **printed name**, not a second execution row. No left
signature rule exists opposite the second client's rule at y=526.02996..526.63.

The preceding associate widget used SignWell y=677, placing its top at PDF
507.75 and its bottom at 525.75, below the associate's printed name in unruled
space. An earlier code comment and its tests incorrectly described this as
an associate execution row. The source image contradicts that description.

All preceding date widgets were only 36 PDF points wide (48 SignWell units).
The existing completed short-form test measured MM/DD/YYYY date text at 49.21
points. This identifies an insufficient allowance, but does not establish the
exact output of a future completed TXR-1501 provider packet.

## Correction

- Selected associate signature/date now use y=566/572, matching the first
  client's row and the broker alternative. The existing role checkbox remains.
- Every date field is widened to 72 SignWell units (54 PDF points), ending at
  the same measured right edge. Dates start at x=312 left and x=696 right.
- Client signature width reduced from 272 to 240 to keep a gap before the date.
- First-client, second-client and broker signature vertical positions, source
  wording, entered terms, recipient identities and signing-order behavior remain
  unchanged. No signature was moved on an executed PDF.

## Verification

- 20 focused test methods pass, including independent source-bound assertions
  for one/two clients and broker/associate variants. The preceding associate row
  and narrow date width deliberately fail those independent assertions.
- Local QA helper now supports `--form 1501` while preserving its default short
  form behavior. It produces only private, explicitly synthetic local previews;
  it cannot contact SignWell or send emails.
- Rendered both two-client role variants and visually inspected their full
  execution pages. Signature placeholders clear printed names and captions;
  complete dates fit within their columns; the second client uses the separate
  lower right rule. Both selected role marks are visible in their source boxes.
- PDF skill workflow required visual review in addition to numerical geometry.
  Initial Poppler font-cache warnings were resolved using a private writable
  font configuration; both final preview renders completed without warnings.
- QA artifacts remain untracked in `tmp/pdfs/txr1501-date-review/`. Only page 6
  was visually reviewed in this change; other source pages were not changed.
- Full discovery: 2,178 tests in 49.107 seconds; 2,176 pass, with the same two
  approved-map reference checks failing. They now also identify the intentional
  TXR-1501 candidate differences. No all-green or full-map approval is claimed.
  Log: `/private/tmp/hof-txr1501-execution-suite.log`.

## Remaining work

Completed-provider TXR-1501 verification remains necessary; synthetic artwork
does not prove SignWell's final signature/date rendering. The existing approved
reference maps are deliberately not regenerated. This new source correction
joins the pending TXR-1507/1905/1914/1917/1919 map differences.

Follow-up: the blank continuation headers and additional populated-value
placement defects have now been corrected locally; see
[long-form value evidence](txr1501-value-candidate-2026-09-18.md).
Do not claim full long-form placement/readiness from this execution correction.

No push, Vercel deployment/build, paid resource, signature invitation, reminder,
customer email or customer-document replacement occurred.
