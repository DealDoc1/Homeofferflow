# Sale contingency layout - September 18, 2026

**Local candidate; not deployed or completed-provider verified.**

## Source and correction

The purchase packet uses the one-page TREC 10-6 dated 12-05-11. Its SHA-256 is
`3b29e372f7d41c0d75b5754969d893a26ea214e54807b689f098fca2da5778ba`.
The source is flat, with no AcroForm fields or page widgets. Neither the source
nor any executed customer document was edited.

The previous answer positions started well inside the available blanks, lacked
width limits, and could clip a long address or monetary amount. Signature/date
pairs did not fit the printed Buyer execution areas; the source has no separate
date blanks at those lines.

- Align answers to measured blanks, using readable embedded Unicode text and
  complete, paginated continuations when answers do not fit. Literal markup
  remains literal and all three existing sale-address aliases are retained.
- Preserve an explicit zero for additional earnest money; an unanswered value
  remains blank. Split valid interview dates into month/day and the last two
  year digits following the source's printed `20`. Reject malformed dates and
  years outside 2000-2099 instead of printing misleading values.
- Align one/two Buyer signature rectangles within their printed execution
  spans and remove the unprinted date fields. Preserve existing signature IDs
  and recipient scope. Initial each continuation and adjust subsequent
  addendum page numbers; uploaded attachments remain unsigned.
- Reject missing selected source or continuation pages explicitly. Retain
  source hashing, record the render revision, and keep production/staging
  renderer sources synchronized.

Blank draft dates remain permitted and the historical missing-key three-day
waiver default is unchanged. This change does not validate the contingency
deadline against closing or complete a broader transaction-term default audit.

## Verification

The PDF skill's source inspection and visual-review workflow was followed.
All six Poppler-rendered pages were visually checked: ordinary two-Buyer terms,
zero earnest money with one Buyer, and a long-answer form plus three
continuation pages. Long answers retain the entire 5,000-character value,
Unicode names and literal markup. Printed text and footer/initial areas remain
separate. Blue QA rectangles show field bounds, not actual signatures.

Four offline production-request cases cover short/long answers and one/two
Buyers using actual rendered packets and generated field maps. Only delivery
is intercepted. Each case retains one request, one combined PDF, and parallel
invitations. Other tests check source geometry, exact text, date validation,
zero/blank distinctions, deselection, missing sources, unique field IDs,
multi-page continuations, subsequent backup-addendum offsets and attachment
placement.

Production-pinned pypdf 4.3.1: 38 focused tests pass. The full suite ran 2,287
tests in 57.793 seconds: 2,285 passed, with only the same two pre-existing
approved-geometry reference failures. No approved reference was overwritten.
Full log: `/private/tmp/hof-sale-contingency-suite.log`.
Bundled pypdf 6.10.0: all 46 expanded focused tests pass, including source audit,
packet bounds and renderer synchronization.

No live submission, customer email, signature, cancellation/replacement,
database mutation, public push or Vercel build/deployment occurred. Private QA
artifacts remain ignored under `tmp/pdfs/sale-contingency-review/`. Existing
release cost and coordinated-migration constraints remain unchanged. This is
not whole-packet visual approval or a completed SignWell signature test.
