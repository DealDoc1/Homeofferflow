# Supabase advisor review - 2026-08-08

## Scope

The live Supabase security and performance advisors were queried after the
authenticated QA-runner hardening release. This is an observation record; it
does not authorize a schema or privilege change.

## Findings

- The security advisor reports several `RLS enabled, no policy` informational
  notices on legacy/server-owned tables.
- The security advisor reports authenticated GraphQL-schema visibility for
  application tables including profiles, brokerage membership, offers, seller
  workspaces, and agent documents.
- The performance advisor reports unindexed foreign keys, unused indexes, and
  an absolute Auth connection limit.

## Decision

No broad grants, revokes, RLS policies, or index changes were applied from the
advisor output alone. HomeOfferFlow uses authenticated Supabase REST reads and
writes from the web client for several of these tables, so revoking the
`authenticated` grant or adding a blanket policy could break production access
or expose data incorrectly. Each table requires an application-path review,
least-privilege policy test, and migration-specific regression before change.

## Access inventory check

The live catalog check found RLS enabled and at least one policy on each
reviewed sensitive table: `hof_profiles`, `hof_agent_profiles`,
`hof_agent_documents`, `hof_brokerages`, `hof_brokerage_members`, `hof_offers`,
`hof_offer_events`, `hof_listing_workspaces`, `hof_seller_leads`,
`hof_seller_disclosure_drafts`, and `hof_subscriptions`. The reviewed policies
are owner- or brokerage-scoped rather than blanket authenticated-user reads.
The remaining GraphQL advisor warnings therefore describe schema visibility,
not proof that every authenticated user can read every row through the app's
REST paths.

## Next safe action

Prioritize a table-by-table access review for buyer/offer data and brokerage
rosters, beginning with authenticated-vs-brokerage-admin visibility. Re-run the
advisors after any approved migration. No production deployment was triggered
by this review.
