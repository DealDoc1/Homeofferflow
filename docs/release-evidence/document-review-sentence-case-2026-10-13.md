# Document review sentence case

- Live baseline `e8e71164f8d6113a2a179763b8d17539e52b63be` passed release `38353191823`. Canonical brokerage card is clean; guided cards use the new plain questions.
- Canonical guided-card check exposed an existing normalizer regression: Review the draft at sentence start became lowercase review the document. This is visible wording, not document data or a signing issue. Do not count the earlier guided-copy review as fully finished.
- Preserve the original first-letter case when replacing review the draft or review the completed draft. Inline wording remains lowercase; sentence starts remain capitalized. No new layer, API, input/control, contractual text, field, role or billing change.
- Actual-source regression against the released tree fails the sentence-case test; the other five language/control tests pass. Corrected tree passes all six. Existing user-control and button-preservation guards remain unchanged. PWA shell v92.
- Verify full candidate/CI/release and the actual canonical card text before marking this boundary finished.
- Full local candidate ran 2,550 tests in 85.545 seconds: one obsolete exact-source assertion expected the previous lowercase replacement. Updated that assertion to the case-preserving callback; no behavior changed after the run. Recheck this focused audit and six actual-source runtime cases, with independent CI/release regression still required.

## Completed checkpoint

- Focused audit: five Python tests pass; actual-source JavaScript runtime: all six cases pass. No controls, stored values or next-step handlers changed.
- PR #1324: https://github.com/DealDoc1/Homeofferflow/pull/1324. Product commit `53dd5338caf3a86af10d7dc4da7b3f2fcfa0c5b0`; exact-head CI `38355171878` passed, including golden rendering, signer geometry and schema preflight. App attachment failed at the existing 100-item limit; the direct PR is intact.
- Protected merge `256b5f4825860d516d116c4adac1674fd5e282f3`; one intentional production release `38355545742` succeeded. Full cloud regression: 2,550 tests in 173.216 seconds, OK (two environment-dependent skips). Prebuilt/schema/canonical/PWA/API/packet checks passed. No routine previews or duplicate test sends.
- READY deployment `dpl_FHFpH89QWFbBuv9LsGkJjMHxxpTY`, `homeofferflow-cslzd8txf-dealdoc1s-projects.vercel.app`. Authenticated deployment inspection confirmed the exact merge SHA and www/non-www canonical aliases.
- Spend snapshot at 2026-10-13 06:17:41 UTC: $0.03 used, $19.97 unconsumed, $3 reserve. This pre-build infrastructure snapshot is separate from Codex limits and is not a billing guarantee.
- Actual canonical signed-in Guided Forms page, after reload: residential-lease and fixture-lease cards both say Review the document at the start of the second sentence. Screenshot `/private/tmp/hof-document-review-sentence-case-live.png`. Read-only card inspection; no Save, Send, checkout or client record changes. Temporary verification tab closed afterward.
- Deployment-scoped error scan 06:18:00–06:20:04 UTC returned no error records; this short window is not proof of zero errors across all traffic.
- This bounded wording slice is complete. Separate TXR-1508 fictional provider test still awaits its packet-specific final disclosure response; no completed-signature visual pass is claimed for it. The overall roadmap remains active.
