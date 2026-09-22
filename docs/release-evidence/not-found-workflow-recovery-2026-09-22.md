# Not-found workflow recovery alignment

Date: 2026-09-22

## Change

- Rewrote all four transaction cards on the not-found page to match the next screen each link actually opens.
- Added source, medium, and campaign parameters to each recovered workflow start so successful recovery traffic can be measured.
- Preserved the direct, low-friction listing and tenant-representation entry paths.

## Customer impact

Visitors who follow a stale or broken link now see accurate expectations instead of being promised an extra menu that will not appear. Each card still takes the visitor directly into the applicable guided workflow.

## Verification

- Public discovery tests assert the four customer-facing descriptions and all tracking parameters.
- PWA and technical SEO coverage verifies the not-found page remains installable, non-indexable, and correctly routed.
