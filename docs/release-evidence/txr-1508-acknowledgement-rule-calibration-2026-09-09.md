# TXR-1508 acknowledgement-rule calibration - 2026-09-09

## Finding

Direct measurement of the approved TXR-1508 source showed that the agent
initials and all acknowledgement-date widgets ended before their printed
rules. Their vertical placement already cleared the adjacent captions.

## Correction

- Agent initials now fill the source rule from x=347 through x=442.
- Each customer initials widget matches its dedicated source rule from x=518
  through x=579.
- Agent and customer dates now fill the date rules through x=746.
- No y-coordinate changed, preserving the existing caption clearance.

## Verification boundary

The renderer and geometry tests lock these source endpoints. A newly completed
SignWell packet remains the required visual confirmation after the next
intentional production release.
