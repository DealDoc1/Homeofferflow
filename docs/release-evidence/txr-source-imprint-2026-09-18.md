# Shared representation source imprint - September 18, 2026

**Local candidate; not deployed or completed-provider verified.**

## Finding and correction

The supplied TXR-1501, TXR-1506, TXR-1507 and TXR-1508 blank sources contain
the supplier office's contact line and account-holder name below the official
form footer. Those two lines were copied into every rendered agreement,
including agreements prepared by an agent from a different office.

Generated copies now remove only those two measured text-showing operations
from each of the four exact reviewed blank sources. The helper checks the
source SHA-256, page count, operation indices, isolated text-block structure,
position and text hashes before changing any page. Unknown/revised files are
left untouched. There is no general name search or broad footer whiteout.

Removal happens on writer-owned blank pages before answer overlays. Thus an
entered agent/client name is not removed even if it matches an imprint name.
It removes actual page content, not merely visible ink under a white rectangle.
No executed document, original source file, form terms, copyright, logo, form
number, page number, initials line or signature geometry is changed.

Each form has a new server render revision, retained in the tracked-request
fingerprint so an existing provider copy is not silently treated as the new
neutral copy. This does not approve replacement/sending of existing requests.

## Verification

- New unit tests verify exact operation removal, retained identical names in
  body text, preserved source-reader content and annotations, unknown/revised
  source passthrough, and atomic rejection of text/position/structure/page
  mismatches. Private source files are not test fixtures in the repository.
- `scripts/qa/txr_source_imprint_qa.py` compares all 15 actual source-based
  rendered pages before/after the change. Every operation except the two
  identified footer operations is retained. At 100 DPI, every pixel above the
  measured bottom 34-point band is identical; only the imprint changes. Form
  identifiers/page counts remain extractable; supplier details no longer are.
- All 15 candidate page images were visually inspected. These are unsigned
  synthetic-data QA copies, not completed-signature placement evidence.
- The same 15-page checks pass under bundled pypdf 6.10.0 and the production-
  pinned pypdf 4.3.1. Version 4.3.1 was installed in an isolated temporary QA
  folder; project dependency pins were unchanged. A whitespace-only extraction
  difference in version 4's form-code text required normalization in the QA
  assertion; pixel comparison and exact operation checks remain strict.
- 35 focused methods pass under pypdf 4.3.1, including render/delivery snapshot,
  recipient preview/render revision and short-form service-term tests.
- Full bundled-runtime discovery: 2,233 tests in 50.341 seconds; 2,231 pass and
  the same two approved signature-map reference checks fail. No approved
  baseline was regenerated. Log: `/private/tmp/hof-source-imprint-suite.log`.

The PDF skill supplied the source-preserving/render-and-inspect workflow.
Official pypdf 4.3.1 content-replacement documentation was checked. Private
outputs remain untracked in `tmp/pdfs/source-imprint-pixel-qa/` and
`tmp/pdfs/source-imprint-pinned-qa/`. Source hashes were rechecked after QA.

No customer email, provider API call, database mutation, push, deployment,
Vercel build or paid resource was made. This covers the four exact source
versions listed in `lib/txr_source_imprint.py`, not every future uploaded PDF.

## Separate follow-up

The visual review also showed TXR-1508 property/customer text close to or on
its printed rules. Those answer baselines need a separate measured placement
review; this footer-only change deliberately does not claim to resolve them.
Completed-provider placement QA and production release remain outstanding.
