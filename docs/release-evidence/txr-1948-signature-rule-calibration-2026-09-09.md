# TXR-1948 signature-rule calibration - 2026-09-09

## Finding

The dormant TXR-1948 SignWell map kept each widget safely above the printed
execution rule and captions, but both widgets ended before the source rule's
right edge.

## Correction

- Buyer widgets now span x=58 through x=394, matching the Buyer rules.
- Seller widgets now span x=424 through x=742, matching the Seller rules.
- The intentional y clearance remains unchanged.

## Verification boundary

TXR-1948 remains an unsigned private-review workflow. The corrected map is
covered by renderer and geometry tests and requires a completed SignWell
packet only if a future release enables signing for this form.
