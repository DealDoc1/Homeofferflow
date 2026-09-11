# TXR-1501 execution-map correction — 2026-09-11

## Change

Correct the TXR-1501 Long Form SignWell execution widgets on page six.
The prior map placed client widgets beside the execution column and placed
broker widgets too high. The corrected map uses the source's actual left and
right execution rules:

- Client signature: source x=324–528, above the `Client's Signature` caption.
- Client date: source x=540–576, above the `Date` caption.
- Broker or associate signature: source x=36–216 on the matching execution
  row.
- Broker or associate date: source x=252–288 on that same row.

## Local verification

- Rendered the corrected SignWell field map over the supplied private
  `TXR1501.pdf` source and visually inspected page six.
- Confirmed first-client, second-client, and selected associate widgets end
  on their printed execution rules and do not cover printed names or captions.
- Ran `tests.test_txr_1501_renderer` and `tests.test_txr_signer_geometry`:
  17 tests passed.

## Scope

This affects new TXR-1501 signing requests only. A document already sent to
SignWell retains the widgets it was created with and cannot be retroactively
repositioned. A newly completed signer PDF remains required for final
provider-rendered visual QA.
