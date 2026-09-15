# Shared form-library request reuse — September 15, 2026

## Outcome

The agent form cards, shared-library list, and seller disclosure picker now
share one authenticated catalog request. A successful result is reusable for
30 seconds in the current browser session. No additional service or dependency
is introduced.

## Session and access boundaries

- The in-memory entry is scoped to both account ID and access token.
- Sign-out explicitly clears it; changed account/token events also clear it.
- A response arriving after a session change is rejected instead of rendered.
- A failed older request cannot evict a newer account's cached response.
- Failed or malformed results are not cached as an empty or available library.
- No catalog or token is persisted to localStorage/sessionStorage.
- This only optimizes library reads. Server-side ownership, approved-source
  revision checks, preparation, and signature-send authorization are unchanged.

## Evidence

The actual loader is executed in Node tests with simulated network responses:
12 concurrent form checks produce exactly one authenticated HTTP request.
Tests also cover expiry, consumer mutation isolation, missing sessions,
malformed/failed responses, refreshed tokens, changed accounts, late responses,
and the shared use of the loader by all three consumers.

Full local regression suite: 1,760 tests passed. This is local implementation
and regression evidence, not a measured production latency or billing saving.

## Release boundary

Built on the pending simultaneous-signing update (PR #1227). No Vercel preview
or production deployment was created for this optimization. The existing
deployment-cost decision remains pending; a goal continuation is not new
authorization to exceed that boundary. The daily 08:00 report should list this
as tested and awaiting bundled release, not deployed.
