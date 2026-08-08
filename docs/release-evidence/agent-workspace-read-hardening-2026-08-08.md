# Agent workspace read hardening — 2026-08-08

## Scope

This bundle hardens the authenticated agent workspace without changing packet
assembly, PDF coordinates, legal-form sources, signer plans, billing, or
production offer-generation behavior.

## Changes

- `0b2287e` resets SignWell and packet-generation metadata when an agent
  duplicates an offer, so the duplicate is always a new unsent draft.
- `9cc8e01` scopes offer-detail reads to the authenticated owner.
- `c2d2b8b` excludes soft-deleted offers from resume and detail lookups.
- `tests/test_offer_duplicate_workspace.py` covers duplicate-state scrubbing,
  owner scoping, and deleted-offer exclusion.

## Verification

- Targeted workspace tests passed.
- Full Python suite passed: 506 tests.
- `git diff --check` passed.
- `scripts/release_preflight.py` passed with no packet/form source or mapping
  change detected.

## Release boundary

No Vercel deployment was triggered for this bundle. It is queued for the next
intentional production release alongside the verified PWA metadata and
post-deploy PWA smoke check. Legal-form source activation remains separately
gated by authenticated QA and completed-signature visual QA.
