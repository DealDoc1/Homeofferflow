# HOA interview and form layout - September 18, 2026

**Local candidate; not deployed and not completed-provider verified.**

## Findings and correction

The current repository HOA source is the one-page TREC 36-11 dated 05-04-2026.
It has no canonical AcroForm fields or page widgets. Its SHA-256 remains
`31c21aeb16ba6c916398211874bbb5a1f62718fc455fc90eb72b70103e8d332f`.
No original form or customer-executed PDF was edited.

The prior renderer placed property/association text starting well inside the
available blank without a width limit. The appraisal packet's long-address
specimen visibly clipped the following HOA page. The same review found
oversized/misaligned checkmarks, Buyer signature/date boxes reaching the
printed execution rules, and an unrepresented choice in Paragraph A(3).

Changes:

- Bound property address, association/phone, selected delivery days and buyer
  fee/reserve limit to measured blanks. Use readable text, locally embedded
  Unicode fonts, and a complete continuation for overflow. Literal markup
  remains literal text; values are not summarized or discarded.
- Place compact marks inside all eight source boxes. Paragraph A(3) now
  reflects the explicit updated-resale-certificate yes/no choice. Deselected
  delivery days and certificate choices do not appear on the form.
- Move Buyer signatures above the printed Buyer rules, with no unprinted date
  fields. Keep existing signature IDs and the one/two-Buyer invitation scope.
  Add initials to every HOA continuation and adjust following addendum pages.
- Missing selected source/continuation pages produce explicit errors rather
  than silent omission. Source hashing continues and a render revision is
  recorded. Production/staging renderer sources remain synchronized.
- Add a conditional interview follow-up for an updated resale certificate.
  Show delivery days only for Seller/Buyer delivery; show the certificate
  question only when documents are already received and approved. Follow-ups
  appear below their triggering question. Keep typed answers when switching
  options, omit irrelevant submitted values, and restore the selected answer
  when resuming a saved draft. Clearing/replacing a draft clears old values.
- Display HOA terms in the review, including zero-dollar caps and the chosen
  certificate requirement. Escape association text in the HTML review.

The new certificate question has no selected default. Missing/invalid choices
for Paragraph A(3) are rejected both by the relevant interview validation and
the renderer; this asks for the actual transaction term, not a new approval,
brokerage-seat or form-source authorization. Other historical server defaults
for old HOA payloads are retained by this change and are not represented as a
completed site-wide default-removal audit.

## Evidence and verification limits

The PDF skill's source-inspection and rendered-review workflow was used. Five
source-backed specimens cover Seller delivery, Buyer delivery, received with
certificate required, received without an updated certificate, and long text
without required delivery. All six pages were rendered with Poppler and
visually checked. Blue rectangles are local QA field bounds, not signatures.
The long specimen includes the complete 400-character address and long
Unicode/literal-markup association name on an initialed attachment.

The preferred agent-browser CLI was unavailable. The existing Playwright
Chrome test pattern provided an isolated real browser, temporary profile and
blocked external requests instead. The actual HOA HTML/styles, visibility
helper, validation fragment and answer collector were exercised at mobile and
desktop widths. Checks passed for conditional fields, missing-choice prompts,
retained answers, submitted values, clearing HOA terms, no horizontal overflow
and no page-script errors. The browser closed after the test. Its collected
`received` answers were used to generate the corresponding rendered PDF.
This is a component/data-to-render check, not a live full-homepage submission,
database persistence or provider-completed signature test.

Four offline production request cases use actual rendered packets and field
maps, intercepting only delivery. They cover one/two Buyers with short/long
answers and preserve one request, one combined packet and parallel invitations.
Tests also cover source-cell bounds, explicit certificate validation, signed
field boxes within Buyer rules, lossless continuation, subsequent sale-addendum
offsets, unchanged uploaded attachment placement and source availability.

Bundled pypdf 6.10.0: 49 focused Python tests pass. The targeted JavaScript
runtime suites pass all 112 cases. Production-pinned pypdf 4.3.1 full suite:
2,279 tests in 56.188 seconds; 2,277 pass and only the same two pre-existing
approved-geometry reference tests fail. The initial run exposed missing helper
wiring in extracted-JavaScript test fixtures; those fixtures now include the
real new helper, and the final run has no new failure. No approved geometry
reference was overwritten. Log: `/private/tmp/hof-hoa-layout-final-suite.log`.

No customer send, signature, cancellation/replacement, database write, public
push or Vercel build/deployment occurred. QA artifacts remain ignored under
`tmp/pdfs/hoa-review/`. Production release constraints are unchanged. Other
purchase forms and their long-answer/signature layouts still require their
own checks; this correction is not whole-packet visual approval.
