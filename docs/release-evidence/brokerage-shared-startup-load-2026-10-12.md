# Brokerage shared startup load

- Current released baseline: `6838c1da42a3778ca9f3a4bc1ea47edeb41fb953`, READY `dpl_HLwSNuF7sB4RiGT95JZvNy6jx2JE`; PR #1319 and intentional release `38285566043` passed independent checks.
- Its canonical browser pass exposed a real incomplete boundary: the authenticated Andrew Gmail agent saw `not connected` while the live database confirmed an active OnDemand membership. Do not treat the previous release as end-to-end verified.
- Startup and tab selection can issue overlapping reads for the same account. A superseded read returns before the newer read finishes, allowing a false unconnected view. An actual-source regression against the released revision reproduces two reads rather than one; the existing 18 isolation/retry cases pass.
- Share only the pending read for the same user ID and session epoch. Other-account requests and responses remain isolated; finished reads are not cached as permanent promises. Failed explicit retries still make one attempt.
- All 19 actual-source runtime cases pass after this correction, including startup plus immediate Brokerage selection. No roles, access grants, database schema, billing, forms, provider requests or credentials change. PWA shell advances to v88.
- One coherent corrective release is needed; use the existing spend guard and no preview. Record full candidate/CI/release and the actual canonical rendered membership after completion below.
- Full final local candidate: 2,526 tests in 88.860 seconds, OK (one environment-dependent skip). A prior test invocation overlapped the mechanical v87-to-v88 edit and produced two stale-version assertions; that run was not pass evidence. The frozen final tree and focused PWA tests pass.

## Released checkpoint and live boundary

- PR #1320 exact-head CI `38331123516` passed; merge `28ce82d08e8a4d5caa3f2f6cb908f9ccb612907c`. Attaching this PR to the chat failed because the app attachment count exceeds 100; the repository PR and direct link remain available. No unrelated attachment was removed to work around the limit.
- Intentional release `38331503781` succeeded, including 2,526 cloud tests in 113.714 seconds (two environment-dependent skips), schema/spend guard, prebuilt deployment and canonical PWA/API/packet checks. READY `dpl_DGAyEvvH8GCeaNjVkX5fppjx2fwV`, exact SHA and canonical aliases verified. Pre-build spend snapshot 2026-10-13 01:21:27 UTC: $0.03/$20 used, $19.97 unconsumed, $3 reserved; not a future guarantee.
- Immediate canonical Brokerage selection still showed a stale unconnected message; returning to that tab after startup correctly displayed OnDemand Realty, active membership. The full live boundary therefore remained incomplete and is corrected separately in `brokerage-late-view-refresh-2026-10-12.md`.
- The separate purchase roadmap row `3dfc123d-4991-4dcf-a1b1-70c0f438cc16` was reconciled through its existing authenticated dashboard editor. Independent database readback confirms production/passed and the scoped completed-provider placement evidence; other addenda remain separately tracked.
- Authenticated canonical Admin Check test status recognized the original provider document as complete without a send or database write. Its generic visual-review hint does not read the saved review result; the actual passed ledger and completed PDF are the review evidence.
