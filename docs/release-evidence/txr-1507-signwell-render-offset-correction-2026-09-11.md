# TXR-1507 completed-artwork offset correction — September 11, 2026

## Release

- Release name: TXR-1507 Short Form completed-signature and date placement correction.
- Git commit / pull request: pending the intentional corrective release.
- Production scope: only the TXR-1507 SignWell execution widgets. The supplied 06-15-26 source, customer interview, recipient plan, and commercial terms are unchanged.
- Changed packet/form target marker: `TXR-1507`.

## Approved source and authorization

- Approved source form/template and version: TXR-1507 Residential Buyer/Tenant Representation Agreement — Short Form, `06-15-26`.
- Source owner and storage: authorized OnDemand Realty private source vault; source bytes are not committed.
- Authority: existing form-use attestation and standing HomeOfferFlow authorization for corrective production fixes.

## Signing plan

- Recipients: one or two Clients and the selected Broker or Broker's Associate.
- Signing order and visibility: each recipient receives only their own required fields; the selected Broker/Associate is identified on the source before signing.

## Completed-signature visual finding and correction

- Completed packet reviewed: `HomeOfferFlow TXR 1507 — 5e7765a4`, completed September 11, 2026 in SignWell.
- Finding: the service-selection mark was contained in its printed square, but completed Client and Broker/Associate signatures and dates rendered on the printed-name row instead of their execution rules. This is a failed placement result, not a release certification.
- Corrected map: all first-row execution fields move down 46 SignWell units (`signature y=734`, `date y=740`); the second Client row receives the same measured adjustment (`signature y=844`, `date y=850`). The shift compensates for the observed SignWell completed-artwork offset while retaining each widget's own signature/date column.
- Local source review: the refreshed source overlay confirms distinct Client, Broker/Associate, date, and selection rectangles with no cross-party overlap. Because SignWell renders completed artwork above the widget rectangle, this local overlay is supporting geometry evidence—not a replacement for the fresh completed packet below.

## Regression

- Dedicated guard: TXR-1507 execution coordinates are locked in renderer, geometry, and privacy-safe SignWell baseline tests.
- Test result: 1,700 tests passed locally after the correction on September 11, 2026.

## Deployment decision

- Ready for production: yes, as a single intentional corrective release.
- Rollback path: restore the immediately preceding production deployment if canonical health checks fail.
- Required post-deploy proof: send and complete one fresh controlled TXR-1507 packet and inspect every X, initial, signature, and date in its completed SignWell PDF. Do not use `5e7765a4` or earlier packets as proof of this corrected map.
