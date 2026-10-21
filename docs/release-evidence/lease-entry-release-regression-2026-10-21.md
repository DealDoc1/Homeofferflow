# Direct lease entry and release regression - October 21, 2026

Status: **implemented locally, focused tested, local browser verified**.
Not deployed. No email, signing invitation, hosted SQL or Vercel usage polling.

The full coordinated regression run started at `6bc2d794` returned exit 1.
Focused reproduction identified three lease landing failures: tests still
assumed a workspace-only handoff, and the new lease flow had reintroduced an
unnecessary task-selection screen. The old launcher fixture also lacked that
new helper, exposing a missing-helper failure rather than exercising fallback.

## Actual user outcome

Selecting **Lease listing** now goes directly into **Who is the landlord, and
which property?**, without asking which lease-listing task to start. Reuse the
existing source-loading/retry path and actual seven-step interview. If the
package helper is absent or declines, retain the lease-context workspace
fallback. Purchase, sale workspace and tenant-representation entry are retained.

The handoff records a real package/direct start only when the interview dialog
is present, never at click time. Existing handoff recovery retains that direct
context. No client/property data is added to telemetry. Source/API selection,
Google address completion, renderers, saving and signing are unchanged.

## Evidence

```sh
../txr1101-runtime/bin/python -m unittest \
  tests.test_agent_landing_funnel \
  tests.test_agent_package_handoff_status_runtime \
  tests.test_agent_document_openers_runtime \
  tests.test_txr1102_interview_runtime -q
```

**69 focused Python tests pass**, including subprocess runtime checks. A direct
Node run of `agent_lease_listing_handoff.runtime.cjs` and
`agent_package_handoff_status.runtime.cjs` passes **10 cases** (already covered
by the Python wrappers, not ten additional independent Python tests).
Tests cover absent/declining helpers, no duplicate workspace, no early start
count, later actual-dialog conversion, and preserved purchase/tenant routes.
Updated assertions match the intended landlord interview rather than retaining
a previous workspace-only destination. `git diff --check` passes.

Extended the existing no-network local interview fixture with
`--lease --transaction-entry` so it extracts the real package helper and actual
transaction launcher, not a replacement click implementation. Its existing
synthetic context API and no-send protection remain intact. Through CUA,
clicking Lease listing opens the real landlord interview, announces the opened
document and does not create the Question 2 task dialog. Desktop and 390x844
phone views were checked; phone has one interview, no horizontal overflow and
no JavaScript errors. No save/send occurred. Screenshots remain outside Git:
`../lease-listing-2026-10-20/ordinary-provider-qa/direct-entry-{desktop,mobile}.jpg`.
The verification skill kept this check bounded to the actual entry -> source
loader/context response -> real interview boundary; it is not a hosted test.

## Release state

GitHub confirms production main still `bfd03d99beca7a13c6009b3adf1c2df7b69d12f1`;
existing draft PR 1353 remains open against main. Git automatic deployments
remain disabled. Completed-provider signing/PDF review and coordinated hosted
source/schema installation are still pending; no evidence is waived or
substituted by the entry fix. The current ordinary sale QA invitation remains
at its final SignWell completion step, not completed. No duplicate invitation
was created.

A full exact-candidate rerun follows this material UI repair; its result will
be appended here rather than launching repeated suites after documentation.
