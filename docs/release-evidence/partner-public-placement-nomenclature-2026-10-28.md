# Public partner placement names and visibility — October 28, 2026

## Change

Public partner surfaces use **Founding Partner**, **Featured Partner**, and
**Premier Partner**. The public directory, partner landing page, application
controls, workflow cards, offer-completion card, home-service guide, and
partner operations copy no longer describe a profile as “Beta partner” or
“Core Partner.” Placements continue to show the Sponsored disclosure.

The partner API derives the Founding designation from the first active profile
in each category using creation time and a stable ID tie-breaker. Directory
results show no more than three profiles per category, preserve that Founding
designation across market filtering, and put the category's active Premier
first. Workflow results continue to return at most one top active Premier
across the platform; the completion renderer also guards against extra Premier
rows. Existing tier values (`founding_pilot`, `monthly_placement`, and
`market_exclusive`), complimentary beta terms, and consumer choice behavior
remain unchanged. The service-worker shell advances to v129 and prewarms the
versioned helper and workflow scripts.

## Verification

- Focused Python tests: 130 passed across partner API, directory, partner tiers,
  public discovery metadata, partner landing, offer completion, and copy audit.
- Node actual-source runtime suites: 34 passed across partner profile,
  provider directory, inspection, and insurance.
- The local partner landing page was inspected in the browser. Names, $0 beta
  terms, tier descriptions, and placement limits appeared as expected.
- Desktop browser review completed. A separate mobile viewport capture was
  unavailable; responsive rules and rendered directory cards are covered by
  source and runtime checks.
- Full regression suite: `python -m unittest discover -s tests -q` passed; 2,941 tests ran, with 23 skipped, in 93.016 seconds.
- No external systems were changed. No messages were sent and no deployment
  was created. Production remains on its previous revision.

## Status

Implemented locally; focused tests passed; local desktop UX reviewed; not
deployed or production-verified. Local checkpoint commit recorded after the passing full
regression run.
