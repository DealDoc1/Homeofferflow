# Focused account handoff — 2026-09-21

## Outcome

After an agent, broker, or investor chooses a specific public workflow,
HomeOfferFlow now takes them directly to the email sign-in step instead of
asking them to choose an account role a second time. The selected transaction
remains preserved for the secure-link return.

The general account-login button still presents Agent, Broker / Team Lead, and
Investor choices when the visitor has not already selected a path.

## Scope, privacy, and cost

- This is a presentation-only reduction in sign-in friction. Authentication,
  role authority, saved profiles, transaction routing, and checkout rules are
  unchanged.
- The focused agent handoff states plainly that no password or brokerage seat
  is required.
- No personal information, transaction data, database object, vendor, preview
  deployment, or recurring cost is added.

## Verification

- Local browser QA confirmed the tenant-representation handoff contains only
  the selected-workflow explanation, email field, secure-link action, and exit
  action; the redundant role chooser is absent.
- Local browser QA then closed that handoff and reopened the general account
  login, confirming all three account-role choices return.
- Runtime coverage verifies signed-in routing, delayed workspace readiness,
  signed-out route preservation, focused copy, and the no-brokerage-seat note.
- 67 focused agent and investor tests plus four route-recovery runtime tests
  pass.
- The complete local regression suite passes: 2,385 tests.
- Production verification remains part of the one coordinated post-reset
  release.
