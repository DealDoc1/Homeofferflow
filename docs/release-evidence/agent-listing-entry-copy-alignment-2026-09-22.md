# Agent listing entry copy alignment — September 22, 2026

## Outcome

The public agent page now describes the actual streamlined property-listing
handoff. Selecting **Property listing** goes directly to the seller and
property question, then the saved listing workspace keeps disclosure
preparation and buyer-offer comparisons together.

This removes the prior promise of an extra task-choice screen that the live
flow intentionally does not show. The visible card, FAQ, and FAQ structured
data now agree with the authenticated transaction-first experience. Purchase,
lease-listing, and tenant-representation behavior is unchanged.

## Verification

- 159 focused agent-entry, listing-workspace, discovery-metadata, and technical
  SEO tests pass with Python 3.12 and the isolated test dependencies.
- `git diff --check` passes.
- No API, database, payment, signing, form-access, or deployment behavior was
  changed.

## Release state

Implemented and locally tested on `codex/listing-entry-copy-alignment`. It is
not production-deployed until included in the next intentional release bundle.
