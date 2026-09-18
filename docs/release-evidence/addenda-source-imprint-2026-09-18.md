# Neutral addendum source footers - September 18, 2026

**Locally implemented and verified; not deployed.**

## Finding

The privately supplied 11-07-2022 blank versions of TXR-1905, TXR-1919,
TXR-1953 and TXR-1954 include the source supplier's office contact details and
account-holder name below the official form footer. Copying those details into
another agent's transaction could misidentify the preparing office.

The supplied TXR-1914, TXR-1917 and TXR-1948 footers were separately inspected;
they do not contain these supplier lines and are not included in this change.
All four affected sources have no canonical editable fields/widgets.

## Correction

Extended the existing narrowly scoped source-imprint helper to the four exact
reviewed source hashes. Each source page loses only two isolated text-showing
operations after hash, page count, text hash, position and structure checks.
Unknown or revised sources remain untouched. There is no heuristic name scrub,
white rectangle, new source approval requirement or brokerage-seat condition.

Removal occurs on newly copied blank pages before answer overlays or appended
continuations. Entered names remain intact, even when identical to a supplier
name. Original blank sources and executed documents are not modified. Official
form terms, TREC attribution, logos, form identifiers and signature/initials
geometry remain unchanged. The update does not claim to correct or approve
any additional signature placement.

The four renderer revisions and authenticated-route revision metadata changed,
so saved signing-request fingerprints distinguish new generated contents from
earlier copies. Existing requests are not silently replaced or resent.

## Verification

- Source-backed before/after checks cover all five affected pages: TXR-1905
  (one), TXR-1919 (two), TXR-1953 (one), TXR-1954 (one). Exact content-stream
  comparison confirms every non-imprint operation is preserved.
- At 100 DPI, only pixels in the measured bottom 34-point footer band change.
  Every pixel above that band is identical; footer details are actually removed
  from extractable text, not merely covered. Official form codes remain.
- All five final source-backed pages were visually inspected after the final
  synthetic-data render. Input source bytes were rechecked unchanged.
- The same source-backed content and pixel checks pass with production-pinned
  pypdf 4.3.1 and bundled pypdf 6.10.0. Local outputs remain ignored under
  `tmp/pdfs/addenda-imprint-pinned/` and `tmp/pdfs/addenda-imprint-bundled/`.
- Expanded unit tests exercise each renderer with synthetic supplier imprints,
  matching entered names and long-answer continuations. They preserve body
  text/annotations, original reader content, unreviewed-source passthrough and
  atomic rejection of structural mismatches. Private PDFs are not repository
  fixtures.
- 58 focused tests pass with production-pinned pypdf, covering source-imprint
  handling, standalone delivery snapshots, lease continuations, mineral and
  loan-assumption purchase packets, and recipient preview/render revisions.

Full production-pinned suite: 2,260 tests in 53.164 seconds; 2,258 passed, with
only the same two pre-existing approved-map reference failures. No new failure
was introduced and no approval baseline was regenerated. Local log:
`/private/tmp/hof-addenda-imprint-suite.log`.

## Operational boundary

No customer records, source-vault records, existing provider documents or
emails were changed. No public push, Vercel build or deployment was triggered.
The release remains bundled behind the separately documented spending and
migration dependencies. The PDF skill supplied the original-preserving,
render-and-verify procedure; this is not completed-provider QA.
