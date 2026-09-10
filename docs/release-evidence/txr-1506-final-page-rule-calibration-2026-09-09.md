# TXR-1506 final-page acknowledgement rule calibration - 2026-09-09

## Finding

The approved TXR-1506 source (revision 06-15-26) was measured directly on
page six in PDF points and converted to SignWell's 96-DPI, top-origin Letter
coordinate system. The existing final-page fields were vertically aligned,
but their signature and date widths stopped before the ends of the printed
rules.

## Correction

- Provider signature: starts after the printed `By:` prefix at x=80 and now
  reaches the signature-rule end at x=384.
- Consumer signatures: use their full printed rules from x=48 through x=384.
- Provider and consumer dates: use the full printed Date rule from x=432
  through x=528.
- Existing y positions remain unchanged because they clear the captions below
  the corresponding rules.

## Verification boundary

Dedicated renderer and geometry tests prevent a narrower future map. This is
source-geometry verification, not a substitute for reviewing a newly
completed SignWell packet after the corrected map is deployed.
