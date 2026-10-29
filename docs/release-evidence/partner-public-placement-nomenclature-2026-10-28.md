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
remain unchanged. The service-worker shell advances to v130 and prewarms the
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

## Founding designation clarity in partner intake

The intake no longer implies that selecting the Founding tier earns a
category's Founding label. It states that the first active partner in each
category receives that public designation regardless of tier. The selected
tier remains a placement preference, and all applicants retain the same
complimentary beta terms.

- A focused regression test confirms the note is present and the misleading
  tier-card badge promise is absent.
- The actual local intake was previously reviewed at 1280x900 and 390x844 with
  a blank form; no application was submitted. The added note is part of that
  same layout and preserves the existing form controls.
- No application, database record, partner message, Stripe action, or
  deployment was created. This change is local only.

The Premier tier copy also avoids promising a fixed 90-day review schedule
during the complimentary beta. It now says “Onboarding and placement review,”
matching the other public placement materials. The focused tier test guards the
exact wording and rejects the old fixed-date claim.

The quick-start form scrolls directly to its five required fields on a phone,
which previously left the category-level Founding Partner rule above the
visible area. The rule now appears immediately before the category field, where
it remains visible during quick-start. The tier UI regression test requires
that placement. The public partner page also uses neutral schema names without
the internal “beta partner placement” phrase, removes the unsupported 90-day
review promise, and keeps its tier comparison anchor visible on mobile.

- Local browser review: the blank quick-start form was inspected at 390×844 and
  1280×900. The category rule is visible before the category selector at both
  sizes; required fields remain legible; the mobile document width stays at
  390px. No application was submitted.
- No external systems, partner applications, messages, agreements, billing, or
  deployments were changed.
