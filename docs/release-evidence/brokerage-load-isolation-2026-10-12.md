# Brokerage workspace load isolation

## Outcome and boundaries

- Opening Brokerage must show the current account's brokerage, never revive an old account or stale roster from a late request, and offer a truthful retry after a load failure.
- Baseline: production merge `967cc0f069a199cdc6623839c205708633b2a382`, READY deployment `dpl_ERYtzaSnfEW78Vyv7ohazaTPsPR1`.
- Scope: existing brokerage loader, account-session reset, brokerage renderer, and PWA shell refresh. No database writes, access grants, credential changes, paid checkout, invitations, customer packets or signing-map changes.
- Live read-only database inspection confirms both owner login profiles are agents with active OnDemand memberships and firm license `9010832`; they are not brokerage admins. This release does not grant new roles or substitute an agent-only view for completed brokerage-admin QA.

## Reproduction and correction

- Runtime tests execute the actual production loader/reset/renderer code with delayed fixture responses. After fixing a test harness's unresolved-promise handling, nine genuine cases failed against the original source; ordinary load was the one passing case.
- Scope each load to its user ID, session epoch and latest request. Check after each asynchronous boundary before changing state. Publish profile, brokerage and membership together after successful reads.
- Remove cached brokerage/membership/roster at refresh and session change. Clear the brokerage display on session change; ignore obsolete success/error callbacks, including a same-user return after sign-out.
- Scope asynchronous brokerage reporting to the current render and brokerage identity. A late roster response or failure cannot replace a newer account's display or cached agents.
- A current load error now has concise customer wording and a Try again action, rather than falsely claiming the user is not connected. Ordinary unconnected accounts retain their enrollment link.
- Retry recovery is read-only and stops if the session changes while loading. No permission or billing behavior is changed.

## Verification

- 18 actual-source runtime cases passed: successful load; sign-out; account switch; same-user return; out-of-order requests; failed refresh; unconnected account; cached roster reset; late summary and error; partial-read error; obsolete error; retry wording; retry recovery; enrollment link; sign-out during retry; same-user profile refresh; single failed-retry attempt.
- Nine focused Python tests passed, including the runtime wrapper, optional platform bootstrap, existing access feedback, profile-default safety and branding propagation.
- Full local release candidate: 2,526 tests in 88.003 seconds, OK (one environment-dependent skip), before the final one-line retry-read deduplication. The refined retry passes the focused actual-source tests; independent exact-head CI verifies the final tree. All 47 inline JavaScript blocks parse; patch whitespace passes. PWA shell advances to v87.
- Full candidate regression, exact-head CI, spend guard, intentional release and canonical browser checks are recorded only when actually completed below.
- Brokerage-admin branding/shared-default/roster/invitation/activation QA and the remaining completed SignWell PDF matrix remain separate roadmap work, not declared passed by these tests.

## Released result and corrective boundary

- PR #1319 final-head CI `38285134148` passed and merged as `6838c1da42a3778ca9f3a4bc1ea47edeb41fb953`. Superseded candidate CI `38284850055` was canceled intentionally, not treated as a product failure.
- Intentional release `38285566043` passed 2,526 cloud tests (two environment-dependent skips), schema/spend preflight, prebuilt deploy and canonical PWA/API/packet checks.
- READY production `dpl_HLwSNuF7sB4RiGT95JZvNy6jx2JE`; exact SHA and canonical domain aliases verified. Spend snapshot 17:41:12 UTC: $0.03/$20 used, $19.97 unconsumed, $3 reserve. Not a future billing guarantee. Error-level deployment sample 17:41:20-17:45:02 UTC had no matching logs.
- Actual canonical Brokerage selection while startup was loading then incorrectly showed not connected for Andrew Gmail. Database membership remained active; no role or data change was used to hide this failure. The overlapping same-session read is addressed and verified separately in `brokerage-shared-startup-load-2026-10-12.md`. This first release alone is not a completed live brokerage pass.
