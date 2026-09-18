# Purchase PDF character preservation audit

## Status and scope

Confirmed local rendering defect; not corrected or deployed. This audit moves
Unicode coverage from an unverified limitation to reproducible failing
evidence. It does not resolve TXR-1507 signature placement, and the real
client's executed PDF was not touched.

Run `scripts/qa/pdf_unicode_audit.py` with the local test dependencies. It uses
the actual purchase adapter with local form sources and synthetic data, not
provider mocks for the rendering boundary. It creates seven unsigned packets
under tmp/pdfs/unicode-audit, with a JSON result and a nonzero exit when any
character-preservation check fails. No network, email, database, signing, or
deployment action occurs.

Each case checks the buyer name on the original contract's first page and the
same text after "Final text:" in the actual appended repair continuation.
Canonical comparison permits equivalent composed/decomposed accents and PDF
line wrapping, but does not remove missing characters or replacement glyphs.

## Results at local commit 5533f56c

| Synthetic case | Main party text | Continuation final text |
| --- | --- | --- |
| Western Latin accents and curly apostrophe | Preserved | Preserved |
| Equivalent decomposed combining accents | Failed | Failed |
| Extended Latin names | Failed | Failed |
| Greek name | Failed | Failed |
| Cyrillic name | Failed | Failed |
| Chinese name | Failed | Failed |
| Curly quotes, dash, fraction, comparison symbol | Preserved | Preserved |

Four of 14 extraction checks pass; ten fail. All packets contain 13 pages.
The audit correctly exits 1, not a misleading green result based on successful
file creation. This is a small representative matrix, not comprehensive
language coverage or a claim about all TXR forms.

Using the PDF skill workflow, visually inspected eight pages: contract page 1
and continuation page 13 for Western Latin, combining accents, extended Latin,
and Chinese cases. Western Latin text is legible; the other three show black
replacement boxes in both locations. Greek/Cyrillic cases currently have
extraction evidence only; do not conflate that with completed visual review.

## Next implementation requirements

- Bundle redistributable, license-documented fonts with the deployment rather
  than depending on the operator's Mac fonts or downloading fonts per request.
- Preserve supplied characters and spelling. Do not strip accents, silently
  transliterate names, replace unsupported text, or rewrite contract terms.
- Use the chosen font's actual metrics for wrapping, fitted blanks, and
  continuation decisions. Changing drawing fonts alone would break the
  source-bound safeguards implemented in the preceding fixes.
- Keep existing ASCII geometry and signature fields stable; verify both
  main overlays and all shared continuation paths with embedded-font output.
- Re-run this exact audit, then visually inspect output and extend coverage
  to other form renderers, mixed scripts, combining marks, and shaping/direction
  requirements. Extraction success alone is insufficient.
- Measure added bundle and packet sizes and rendering cost. No paid font
  service or external rendering provider is required by this plan.

The local runtime contains Noto Sans and DejaVu candidates, but neither has
been copied into the project, licensed for this package by assumption, or
proved sufficient for the whole character set. The repository currently has
no bundled TTF/OTF font assets. The audited paths use Helvetica. These facts
guide the next font-selection work, not a claim that a candidate font is ready.

No product source, source PDF, customer document, production data, dependency,
or subscription was changed in this audit. Existing regression results from
the prior turn remain historical; the full product suite was not rerun for
this QA-only addition. Include the finding as in-progress local work in the
daily report, not a deployed fix or a user-approval blocker.
