# Standalone PDF deployment assets - September 18, 2026

**Local correction. Not built on Vercel, uploaded or deployed.**

## Finding and correction

The standalone-form endpoint `api/admin-dashboard.py` calls the shared TXR
renderers, which now use `lib/pdf_text.py` for names and long-answer text.
Its function configuration still excluded `lib/fonts/**`. An extended-character
name could therefore pass local rendering tests but fail when those assets were
absent from the deployed function. Existing font tests incorrectly required
that exclusion for every function except the purchase-packet endpoint.

The standalone endpoint now explicitly includes the same font directory and
licenses as the purchase endpoint. Other function exclusions are unchanged:
non-PDF services still omit the approximately 10.7 MiB of font assets. There
is no new runtime dependency, external font request, service, or billing plan.
This follows Vercel's documented project-root `excludeFiles` behavior for
[Python function bundles](https://vercel.com/docs/functions/runtimes/python).

Private `tmp/` and `output/` directories are now explicitly excluded by both
`.gitignore` and `.vercelignore`. This protects local completed-provider PDFs,
screenshots and generated deliverables from accidental future inclusion in
commits and CLI uploads. Existing files remain in place. No prior disclosure is
alleged or established by this review. See Vercel's
[deployment exclusion documentation](https://vercel.com/docs/deployments/vercel-ignore).

## Verification

- 27 focused tests pass with both the bundled dependency and production-pinned
  pypdf 4.3.1, including the child interpreter's explicit version assertion.
- A new isolated test copies `lib/` through the current function exclusion
  patterns and launches a fresh interpreter. It discards the checkout's
  PYTHONPATH and verifies that no fallback font was already registered.
- Actual TXR-1501, TXR-1506, TXR-1507 and TXR-1508 renderers produce eight
  synthetic packets: normal and long-answer variants for each. Extended Latin,
  Vietnamese and Chinese name text survives extraction, and every long-answer
  continuation preserves its final answer. Source pages are generated blanks;
  no customer or restricted source PDF is needed for these tests.
- A negative test omits the fonts and reproduces the missing-font failure.
- Font/license availability is checked for both PDF endpoints and exclusions
  remain checked for every non-PDF function. Ignore entries and whitespace
  checks pass. Git's ignore check confirms the private artifact directories.
- The first full pinned-dependency run revealed four TXR-1917 subtest failures
  in an existing text-only comparison: pypdf inserted an inferred space between
  a days value and a distant checkbox in the draft but not in its signing copy.
  Independent pdfplumber character/position comparison confirms that every
  non-name glyph is identical. That regression now compares actual glyphs and
  coordinates rather than extractor-generated spacing, with a negative test
  proving moved or missing marks are detected. No form renderer was changed.
- Final full discovery using pypdf 4.3.1: **2,252 tests in 49.599 seconds;
  2,250 pass and the same two approved-map reference comparisons fail**.
  Those are `test_every_current_map_matches_the_source_calibrated_baseline`
  and `test_current_released_maps_match_the_approved_baseline`. Their reference
  files remain unchanged; no all-green or completed-provider claim is made.
  Local log: `/private/tmp/hof-pdf-assets-final-suite.log`.

The file-set test is a deliberately limited simulation of the current flat
exclusion patterns, not Vercel's actual bundler. It proves runtime access to
these assets under the tested configuration, not deployed bundle size, visual
placement or completed-provider behavior. No drawing or signing coordinates
were changed in this correction. Earlier visual/provider evidence retains its
original scope; this test does not extend it.

## Release status

No GitHub push, Vercel build/deployment, customer email, signing request,
database mutation or paid resource occurred. Automatic Git deployments remain
disabled. Completed-provider coverage for the remaining signing variants and
the deliberate production release are still outstanding.
