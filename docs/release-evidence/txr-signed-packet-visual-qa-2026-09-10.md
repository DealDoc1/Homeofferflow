# TXR completed-signature visual QA - 2026-09-10

## Scope

Read-only visual inspection of the completed SignWell packets saved locally on
2026-09-08. This records observed rendering evidence; it is not a production
activation record and does not replace a fresh completed-packet check after
the pending signer-map bundle is released.

| Form | Completed packet result | Current source-map status |
| --- | --- | --- |
| TXR-1501 | Not passed. The client date crowded the printed `Date` caption, and the associate completion details landed below the intended execution rule. | Corrections were committed after this packet was created (`2459b48`, `b68b166`, and `7408907`). They require a newly completed packet for visual verification. |
| TXR-1507 | Not passed. Both client dates crowded their printed `Date` captions, and broker/associate completion details were below the intended execution rule. | Correction `a7901ac` was committed after this packet was created. It requires a newly completed packet for visual verification. |
| TXR-1508 | Passed for the inspected one-customer packet. Broker and customer initials and dates were visually seated on their intended rules without caption overlap. | Current map also has local geometry and renderer coverage. A separate multi-customer packet remains outside this one-customer inspection. |

## Evidence method

- Rendered every page of the three completed PDFs at 160 DPI and inspected the
  execution areas visually.
- Re-ran the current signer geometry, TXR-1501 renderer, TXR-1508 renderer,
  and signing-request-path checks: 33 tests passed.
- Re-ran TXR-1507 geometry and signing-request-path checks: 25 tests passed.

## Release decision

Do not change TXR-1501 or TXR-1507 to completed-signature visually verified
based on the older packets. After the next intentional production release,
create and complete fresh controlled packets using the current signer maps,
then inspect all signer and date fields before updating their QA status.

