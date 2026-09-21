# Standalone appraisal-addendum answer correction - September 18, 2026

**Local candidate; not deployed or completed-provider verified.**

## Reproduced defects

The supplied TXR-1948/TREC 49-1 source (11-15-2018) has eleven canonical editable
fields/widgets: four text fields, three choices and four signature fields.
Before correction, an allowed 400-character property address was visibly
clipped by its fixed-size field. Long buyer/seller names crossed into each
other's execution areas, and a supported Unicode name displayed a black box.
The original source and the existing client-executed PDF were not edited.

Stored and visible values also required separate checks: production-pinned
pypdf 4.3.1 could serialize a newly assigned Unicode string without the UTF-16
marker, producing raw bytes when the completed PDF was read back.

## Changes

- Shared, source-measured answer layout bounds the property address, selected
  appraisal amount/time and preview party names. Values that cannot fit at a
  readable size reference a paginated exhibit containing their complete text.
- All continuation pages receive required initials for the same named Buyers
  and Sellers. Preview and signing copies produce identical continuation
  counts; signing copies omit names from the execution lines.
- Editable field values and their appearances now use the same laid-out text.
  Unicode text is stored with its proper encoding marker and displayed using
  locally embedded fonts. Fields remain interactive; the document is not
  flattened, and canonical fields and page widgets remain linked.
- Appearance streams are valid indirect PDF objects with their own embedded
  resources. Actual viewer rendering is checked in addition to extraction;
  testing only an isolated stream can miss a blank-looking page widget.
- Unselected amounts/days are cleared from both stored values and visible
  appearances. Existing signed-source/schema-ambiguity rejection remains.
- Base SignWell signature rectangles are unchanged. The non-interactive source
  fallback now uses the same bounded text layout and compact source-cell marks.
- Render/signing revisions distinguish the new contents without introducing
  another source-owner approval, brokerage-seat or preparation requirement.

## Verification

New regression tests cover all three appraisal choices, canonical/widget value
agreement, exact text from actual appearance streams, valid indirect stream
references, glyph bounds, Unicode names/addresses, literal markup, full long
values, unchanged input data and preview/signing page-count agreement.

The actual offline render-and-send path is exercised using the repository's
editable appraisal source, not a mocked renderer. Eight scenarios cover short
and long answers for all four Buyer/Seller count combinations. They verify the
same recipients, every appended page initialed, unique field IDs, one source
download, one send and simultaneous invitations. Network calls are mocked;
this is not live email delivery or completed SignWell evidence.

Source-backed visual QA used the separately supplied private TXR-1948 source:
one ordinary Unicode partial-waiver page, a two-page long-answer preview and
a two-page signing copy. All five final pages were inspected after Poppler
rendering, including the actual editable appearances, legible Unicode text,
clear execution lines and complete continuation. The original one-page failing
specimen is retained privately as before-correction evidence. No private PDF
or generated specimen is included in the commit.

39 focused tests pass with production-pinned pypdf 4.3.1 and bundled pypdf
6.10.0. Full production-pinned suite: 2,265 tests in 53.537 seconds; 2,263 pass
and only the same two pre-existing approved-geometry reference tests fail.
No new failure was introduced. Local log:
`/private/tmp/hof-appraisal-answer-final-suite.log`.

## Scope and release boundary

This corrects the standalone TXR-1948 renderer. The combined purchase-offer
appraisal addendum uses a separate rendering path and is not represented as
verified by these checks. Existing completed-provider evidence is not extended
to these new continuation pages. No approved signature baseline was replaced.

The PDF skill supplied the dual canonical/appearance and render-and-verify
procedure. No customer document, database row, provider request or email was
changed. No public push, Vercel build, preview or deployment was performed.
Local QA files remain ignored under `tmp/pdfs/appraisal-answer-review/`.
