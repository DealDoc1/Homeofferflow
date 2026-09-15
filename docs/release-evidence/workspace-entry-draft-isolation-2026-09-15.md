# Workspace and sign-in entry preserve unfinished offers

## Confirmed issue and local fix

The previous homepage isolation fix did not cover dedicated Agent and Investor
links. Those handlers called the transaction-changing audience selector before
opening a workspace or sign-in prompt. Separately, both base and enhanced
`setAuthRole` implementations assigned the login choice to the current offer.

- Agent entry, delayed entry after auth readiness, and load-time route recovery
  now use presentation-only audience selection.
- Investor workspace entry and the installed-app shared-context agent chooser
  do the same.
- Opening sign-in or changing its Agent, Broker, or Investor tab still updates
  sign-in context and its remembered preference, but not the unfinished offer.
- Actual new-offer commands remain responsible for selecting the transaction
  role. Existing account-offer runtime tests verify agent, broker, and investor
  starts still select their intended interviews.

## Verification

- Full local suite: **1,999 tests pass in 16.903 seconds**.
- The audience-isolation harness now contains 76 passing runtime cases,
  including 42 new cases for this batch. Against pre-fix commit `2065ecb0`,
  all 42 new cases fail and the preceding 34 still pass.
- Real source-backed handlers cover four agent transaction choices, normal
  and recovery routes, signed-in/out entry, dashboard/listing/relationship
  workspaces, investor account matches/mismatches, both sign-in implementations,
  all three sign-in tabs, and the shared-context agent action.
- Tests assert unchanged offer data and object identity, step, representative
  input/helper state, and no draft-save/step-reset calls. Destination handlers
  and account-loading operations are mocked: these tests verify the handoff,
  not authenticated production workspace loading or complete transactions.
- Existing slow-workspace recovery and explicit new-offer controls pass.
- All 45 executable inline scripts parse; the shared-target asset parses;
  `git diff --check` passes.

## Auth review and limits

Used the Supabase skill security checklist and reviewed the current changelog
and passwordless sign-in documentation. Markdown retrieval was unsupported by
the web reader; official HTML documentation was available:

- https://supabase.com/changelog
- https://supabase.com/docs/guides/auth/auth-email-passwordless

This is client-side navigation/state isolation only. No Supabase auth API,
session token, email redirect, database query, migration, RLS policy, profile
authority, or server authorization behavior changed. No live test sign-in,
customer email, or production data mutation was performed. No database test
query was needed because no database operation was changed.

## Release status

Local only; not pushed or deployed. No Vercel build or preview, new service,
subscription, or background request added. Keep this in the next authorized
cost-controlled release and the daily report's locally verified work section.
