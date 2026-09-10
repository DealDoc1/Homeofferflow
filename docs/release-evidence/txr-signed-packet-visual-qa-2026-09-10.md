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
| TREC 20-19 purchase packet with Seller's Temporary Residential Lease | Historic packet did not pass as current visual proof. On the execution page, both buyer signature/date pairs sat above the intended execution rules; the buyer-side Seller's Temporary Residential Lease signatures were similarly elevated. The packet was created before the current full four-party execution routing. | The current production map includes all four execution parties and their matching dates, plus distinct landlord/tenant lease signature rows. Focused geometry and production-signing checks passed on 2026-09-10. A fresh completed four-party packet is still required for a post-release visual pass. |

## Evidence method

- Rendered every page of the three completed PDFs at 160 DPI and inspected the
  execution areas visually.
- Re-ran the current signer geometry, TXR-1501 renderer, TXR-1508 renderer,
  and signing-request-path checks: 33 tests passed.
- Re-ran TXR-1507 geometry and signing-request-path checks: 25 tests passed.
- Rendered and inspected the 15-page completed 20-19/15-7 SignWell packet,
  including the main execution page and both lease pages. The audit report
  shows two buyer recipients completed it; the historic packet predates the
  current four-party production map.
- Re-ran current 20-19 Seller's Temporary Residential Lease geometry and
  production-signing checks: 9 tests passed.

## Release decision

Do not change TXR-1501, TXR-1507, or the combined 20-19/15-7 packet to
completed-signature visually verified based on the older packets. After the
next intentional production release, create and complete fresh controlled
packets using the current signer maps, then inspect all signer and date fields
before updating their QA status.
