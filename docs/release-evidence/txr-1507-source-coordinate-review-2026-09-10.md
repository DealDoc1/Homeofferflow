# TXR-1507 source-coordinate review - 2026-09-10

## Scope

- Form: TXR-1507 Residential Buyer/Tenant Representation Agreement - Short Form
- Source: approved local `TXR1507.pdf`, revision `06-15-26`
- Review: page-two execution rows and page-one initial fields
- Purpose: correct the existing electronic field map after completed-packet review showed that its page-two widgets did not sit on the printed lines.

## Measured page-two execution rules

The source is US Letter (612 x 792 PDF points). The SignWell map uses the
96-DPI, top-origin coordinate system; source measurements therefore use a
4/3 conversion.

| Source execution rule | Source PDF coordinates | SignWell rectangle used |
| --- | --- | --- |
| Broker/Associate signature | x 36.0-288.1, y 534.0 | x 48, y 688, 240 x 24 |
| Broker/Associate date | right-hand segment of the same rule | x 336, y 694, 48 x 18 |
| Client 1 signature | x 324.1-576.1, y 534.0 | x 432, y 688, 272 x 24 |
| Client 1 date | right-hand segment of the same rule | x 720, y 694, 48 x 18 |
| Client 2 signature | x 324.1-576.1, y 616.8 | x 432, y 798, 272 x 24 |
| Client 2 date | right-hand segment of the same rule | x 720, y 804, 48 x 18 |

The corrected fields finish at the actual printed rules (SignWell y 712 for
the first execution row and y 822 for the lower Client row). They no longer
occupy the blank space above the execution rows or the printed signature/date
captions.

## Automated safeguards

- `tests/test_txr_1507_renderer.py` covers the one- and two-client maps.
- `tests/test_txr_signer_geometry.py` guards all six corrected page-two rectangles.
- `tests/fixtures/txr_signwell_geometry_baseline.json` makes any later geometry drift fail CI.
- The full local regression suite passed after this correction: 1,686 tests.

## Release status

This is source-coordinate and local-regression evidence. It does **not**
represent a new completed SignWell packet: the already completed packet cannot
be altered. The corrected source map is included in the next intentional
production batch, after which a fresh controlled two-client packet must be
completed and visually inspected before this item can be recorded as
completed-signature visual QA.
