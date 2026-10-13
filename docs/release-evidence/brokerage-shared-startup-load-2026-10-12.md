# Brokerage shared startup load

- Current released baseline: `6838c1da42a3778ca9f3a4bc1ea47edeb41fb953`, READY `dpl_HLwSNuF7sB4RiGT95JZvNy6jx2JE`; PR #1319 and intentional release `38285566043` passed independent checks.
- Its canonical browser pass exposed a real incomplete boundary: the authenticated Andrew Gmail agent saw `not connected` while the live database confirmed an active OnDemand membership. Do not treat the previous release as end-to-end verified.
- Startup and tab selection can issue overlapping reads for the same account. A superseded read returns before the newer read finishes, allowing a false unconnected view. An actual-source regression against the released revision reproduces two reads rather than one; the existing 18 isolation/retry cases pass.
- Share only the pending read for the same user ID and session epoch. Other-account requests and responses remain isolated; finished reads are not cached as permanent promises. Failed explicit retries still make one attempt.
- All 19 actual-source runtime cases pass after this correction, including startup plus immediate Brokerage selection. No roles, access grants, database schema, billing, forms, provider requests or credentials change. PWA shell advances to v88.
- One coherent corrective release is needed; use the existing spend guard and no preview. Record full candidate/CI/release and the actual canonical rendered membership after completion below.
- Full final local candidate: 2,526 tests in 88.860 seconds, OK (one environment-dependent skip). A prior test invocation overlapped the mechanical v87-to-v88 edit and produced two stale-version assertions; that run was not pass evidence. The frozen final tree and focused PWA tests pass.
