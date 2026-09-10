# TXR-1953 signature-rule calibration - 2026-09-09

## Finding

Direct measurement of the approved TXR-1953 source showed that all four
signature widgets ended materially before the right edge of their printed
Buyer or Seller rule. Their vertical placement already ended exactly at each
source rule, above the printed party captions.

## Correction

- Buyer signature widgets now span x=70 through x=376, matching the printed
  Buyer rules.
- Seller signature widgets now span x=440 through x=742, matching the printed
  Seller rules.
- No y-coordinate changed, preserving the existing caption clearance.

## Verification boundary

The renderer and geometry tests lock these source endpoints. A newly completed
SignWell packet remains the required visual confirmation after the next
intentional production release.
