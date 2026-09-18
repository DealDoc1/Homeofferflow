# Purchase PDF character preservation correction - September 18

## Status and scope

Implemented and verified locally, not deployed. This change covers the shared
20-19 overlay and repair, non-realty, lease, and contract-terms continuation
rendering helpers. It does not change the separate TXR renderers or SignWell
signature placement. No production build, preview, or deployment was started.

## Correction

- Supported ordinary text retains Helvetica and identical width measurements.
- Display-only NFC composition preserves canonically equivalent accents without
  changing stored answers. Existing render metadata may still be appended by
  the adapter; original answer values remain unchanged.
- Embedded local Noto Sans and static CJK fallback fonts supply missing glyphs.
  Font provenance, copyright, licenses, build command, and hashes are recorded
  in `lib/fonts/README.md`. Fonttools is a build-only tool, not a server runtime
  dependency. No request-time external font download is needed.
- Fitting and drawing use the same font runs and actual glyph metrics.
- A single PDF text object preserves mixed-font words in text extraction;
  separate draw operations initially introduced gaps within a Vietnamese name.
- Continuation markup escapes user text before adding controlled font tags.
- Unsupported characters raise a rendering error rather than silently becoming
  black boxes. This is not a claim of universal language, emoji, RTL, or complex
  script shaping support.
- The PDF function explicitly includes fonts and licenses; other explicitly
  configured functions exclude them. Actual deployed bundling is unverified.

## Verification

- Seven synthetic audit cases / fourteen text checks now pass, compared with
  four passes and ten failures in the preceding audit. Cases: western Latin,
  decomposed accents, extended Latin/Vietnamese, Greek, Cyrillic, Chinese,
  and mathematical/typographic punctuation. All packets remain thirteen pages.
- Re-rendered and visually inspected pages 1 and 13 of all seven final packets
  (fourteen pages). Tested characters are visible, names remain on their lines,
  and continuation text has no missing-glyph boxes or overlapping lines.
- Nine new regression tests cover actual PDFs, unchanged answer values, exact
  ASCII metrics, equivalent accents, mixed-font word extraction, embedded font
  resources, escaping, unsupported characters, all shared continuation types,
  measured inline fitting, and explicit function asset configuration.
- Focused suite: 66 tests pass in 18.544 seconds.
- Full suite: 2,107 tests in 38.482 seconds; 2,105 pass. The same two TXR-1507
  approved-map reference checks fail while the corrected signature map awaits
  completed-provider QA. No other full-suite failure was reported.
- Each thirteen-page audit packet is about 2.11-2.15 MB. A direct mixed-font
  overlay embeds only subsets and remains below the tested 150 KB bound. The
  local CJK asset is about 10 MB; it is not embedded wholesale in each PDF.

Generated forms and PNGs remain private scratch artifacts, not repository
assets. No customer document, signature, agreement, or saved answer was edited.
