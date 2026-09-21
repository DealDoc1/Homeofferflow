# TXR-1501 long-answer continuation - September 18, 2026

**Implemented, tested and visually reviewed locally. Not deployed or verified
in a newly completed SignWell packet.**

## Change

The long-form renderer now places complete answers in measured source blanks,
using readable text at 7 points or larger. If the whole answer cannot fit,
the blank refers to an attached answer continuation containing the full value.
No answer is silently cut off. Multi-line party and market-area blanks are used
before adding a continuation. Ordinary answers still produce six pages.

Paragraph 16 lists and checks the answer-continuation attachment when present.
Every appended page includes required initials for each actual client and the
selected broker or associate. There are no added recipients or user steps.
The server derives extra signing fields from the PDF it just rendered, not a
page count supplied by the browser. The same rendered PDF is sent to SignWell.
The unpublished map identifier is now
`txr-1501-2026-09-18-continuation-candidate-v4`; existing stale-copy checks apply.
Existing sent/signed packets are not modified.

Source: private TXR-1501, 06-15-26, six pages, SHA-256
`d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd`.
No source PDF or customer information is included in this commit.

## Verification

- 48 focused tests pass across overflow, source bounds, headers, renderer,
  footer initials, execution positions and server signing-field dispatch.
- Long-value tests exercise both roles and one/two clients, preservation of
  every complete value, unbroken strings, Unicode and literal markup, source
  bounds, minimum font size and required initials on every appended page.
- Dispatcher tests ignore a bogus browser page count and use the actual PDF.
- Full suite before the identifier-only update: 2,193 tests, 2,191 pass; the
  same two approved-reference-map comparison tests fail. They are not hidden
  or regenerated. Log: `/private/tmp/hof-txr1501-overflow-suite.log`.
- Rendered two synthetic eight-page specimens from the private source. Reviewed
  all eight associate pages, plus both broker continuation pages. Answers,
  references, attachment checkbox and synthetic initials are readable and clear
  of printed text. These are requested-geometry previews, not actual signatures.
- Private QA files are under `tmp/pdfs/txr1501-overflow-review/`, untracked.

## Not yet established

Actual completed-provider placement remains unverified for this long-form
candidate. Both roles and one/two-client configurations need completed-packet
review before replacing approved references. This does not assert that the
entire transaction journey or every form is production-ready.

No push, deployment, Vercel build, database mutation, provider request, customer
email, reminder, charge or new resource occurred. Customer agreements and source
files remain unchanged. The PDF review skill supplied the render-and-inspect
workflow; text extraction alone was not used as visual proof.
