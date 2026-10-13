# Document review sentence case

- Live baseline `e8e71164f8d6113a2a179763b8d17539e52b63be` passed release `38353191823`. Canonical brokerage card is clean; guided cards use the new plain questions.
- Canonical guided-card check exposed an existing normalizer regression: Review the draft at sentence start became lowercase review the document. This is visible wording, not document data or a signing issue. Do not count the earlier guided-copy review as fully finished.
- Preserve the original first-letter case when replacing review the draft or review the completed draft. Inline wording remains lowercase; sentence starts remain capitalized. No new layer, API, input/control, contractual text, field, role or billing change.
- Actual-source regression against the released tree fails the sentence-case test; the other five language/control tests pass. Corrected tree passes all six. Existing user-control and button-preservation guards remain unchanged. PWA shell v92.
- Verify full candidate/CI/release and the actual canonical card text before marking this boundary finished.
- Full local candidate ran 2,550 tests in 85.545 seconds: one obsolete exact-source assertion expected the previous lowercase replacement. Updated that assertion to the case-preserving callback; no behavior changed after the run. Recheck this focused audit and six actual-source runtime cases, with independent CI/release regression still required.
