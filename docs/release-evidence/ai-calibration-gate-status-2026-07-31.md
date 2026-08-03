# AI offer-review calibration gate status

## Automated verification

The current branch passes all 386 automated tests covering:

- the five required calibration scenario identifiers;
- feedback API validation and scenario tracking;
- bounded offer-review behavior and dashboard copy;
- the expert calibration worksheet;
- calibration tracker reconciliation and production safeguards.
- browser-side enforcement of the product-approved educational disclaimer.
- structured browser-side capture of calibration evidence dimensions and
  required reviewer disposition.

The current production release is `d9eb70b` (2026-08-03), deployed as
`dpl_9ouocpBidjaTrC7feae4UHHFEJzs`. It adds structured calibration evidence
capture without changing AI scoring or wording.

## Human evidence status

The live feedback table currently contains zero records with a calibration
scenario identifier. Therefore the AI offer-review feature remains limited
educational functionality and is not treated as expert-calibrated.

The required human evidence is five anonymized broker/experienced-agent
reviews covering:

1. strong seller market;
2. balanced market;
3. stale listing;
4. cash offer; and
5. financed offer with a material contingency.

Each review must record useful, misleading, insufficient, and missing output,
disclaimer behavior, and the reviewer disposition before any scoring or
wording change is released.

## Release decision

Automated safeguards are ready. No AI scoring or wording change is approved by
this record. Human calibration evidence remains pending.
