# Brokerage late view refresh

- Outcome: an agent who opens Brokerage while Account is initializing should see the correct connection when startup finishes, without clicking away and back. Keep the user's selected tab and profile edits intact.
- Baseline: `28ce82d08e8a4d5caa3f2f6cb908f9ccb612907c`, production READY `dpl_DGAyEvvH8GCeaNjVkX5fppjx2fwV`. The canonical HTML SHA-256 matches the local release exactly: `d2fc81e390a967c89074408f2000f2b7078beb0979d1bdb3f3990877022b52bb`.
- Actual immediate Brokerage selection still showed not connected. Selecting Dashboard then Brokerage showed the correct OnDemand Realty connection and active membership immediately. This isolates a stale rendered view after a later startup load, not missing membership or a need for new roles. Read-only policy inspection confirms own-profile/own-membership reads and member-scoped brokerage visibility; no policy was changed.
- A current load completion refreshes only the still-active Brokerage pane when it has a successful connection or a truthful load error. No tab navigation, extra read, credential, billing, invitation, customer data or signing change. Unconnected accounts retain their normal existing path; inactive panes are not touched.
- Actual-source tests against the released baseline reproduce both stale successful connection and stale failed-load display. All 22 isolation/shared-load/view-refresh runtime cases pass after the correction. PWA shell advances to v89.
- Freeze the candidate before full tests. Record full suite, independent exact-head CI, one spend-guarded production release and the actual immediate-tab canonical check below; source inspection is not a live pass.
- Frozen full local candidate: 2,526 tests in 85.382 seconds, OK (one environment-dependent skip). All 47 inline scripts parse; patch whitespace passes.

## Released and actual production-verified result

- PR #1321 exact-head CI `38332498219` passed; merge `30cf21f132f80bb9563356e568f6d62df12844f6`. Chat attachment failed at the app's 100-attachment limit; the PR remains accessible directly.
- Intentional release `38332814162` succeeded. Cloud candidate: 2,526 tests in 169.355 seconds, OK (two environment-dependent skips); schema/spend guard, prebuilt deploy and canonical PWA/API/packet checks passed.
- READY production `dpl_H1DPfRjcM6wpjmnjAYSkckRobRD8`, `homeofferflow-ehqjuu7nc-dealdoc1s-projects.vercel.app`, exact release SHA and canonical domain aliases verified.
- Pre-build spend snapshot 2026-10-13 01:38:45 UTC: $0.03/$20 used, $19.97 unconsumed, $3 reserve. This is Vercel infrastructure credit, not Codex usage or a future billing guarantee. No preview deployments or billing changes.
- Actual canonical owner check: in one uninterrupted browser action, reload, open Account and immediately select Brokerage. Dashboard startup aria-busy was true and Brokerage initially showed Loading. Without clicking or changing tabs, startup became false and Brokerage remained active, showing OnDemand Realty, connected, membership active. This verifies the original late-render boundary, not just a settled-tab reselect.
- Screenshot: `/private/tmp/hof-provider-completion.bBz0N0/live-brokerage-startup-refreshed.jpg`. No profile save, access grant, invitation, checkout or real signing operation occurred in this check.
- Error-level deployment log sample 2026-10-13 01:38:50-01:43:07 UTC: no matching logs. This is a bounded sample, not a universal error-free claim.
