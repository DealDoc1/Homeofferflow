# TXR-1954 signature-rule calibration - 2026-09-09

## Finding

Direct measurement of the approved TXR-1954 source showed that the existing
Buyer and Seller signature widgets reached the correct vertical signing rows
but ended well before the right edge of every printed rule.

## Correction

- Buyer signature widgets now span x=64 through x=399, matching the Buyer
  rules.
- Seller signature widgets now span x=418 through x=742, matching the Seller
  rules.
- No y-coordinate changed, preserving the existing clearance from the party
  captions beneath the rules.

## Verification boundary

The renderer and geometry tests lock these source endpoints. A newly completed
SignWell packet remains the required visual confirmation after the next
intentional production release.
