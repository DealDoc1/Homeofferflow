# Profile edit preservation

## Batch contract

- Outcome: agent/investor edits survive late saved-profile rendering and tab changes until successfully saved or deliberately discarded.
- Scope: existing profile editor presentation/render/save lifecycle; memory-only touched-field cache. No new field, endpoint, permission, source, signature, pricing, database mutation or dependency.
- Production baseline `2bdcd5b7cd06a55aa0249e45e70c0f76f8d5830a`, READY `dpl_9vV2Y2BjG7x8bxeTdkmivyty8n4p`.
- Cost: one full local candidate run, green review and one guarded prebuilt release; no previews, test documents or emails.
- Evidence: actual source renderer with fictional edit/render/save/failure/identity cases, then a controlled unsaved production marker restored through Discard without clicking Save.

## Cause and implementation

- Existing base renderer replaces the entire profile form with `innerHTML`; later wrappers add defaults and IABS cards. A late startup render therefore replaces values and focused controls an agent may already be editing.
- Eight relevant regression cases failed before the helper existed. A fixture dependency error was fixed before counting these failures; that error is not represented as an application defect.
- The helper wraps the final existing renderer, delegates its original behavior, snapshots the fresh defaults and restores only changed profile controls. Untouched inputs receive new saved defaults normally.
- Explicit empty values, zeroes and selected choices are preserved. Derived edits differing from the last rendered baseline are also captured. Changed fields retain cursor/focus only when Profile is the visible panel.
- Cache is private in-memory state scoped by login identity, agent/investor schema and session epoch. No local/session storage, network request, new role grant or credential access. File/password/hidden/credential-like controls are excluded.
- Logout/account/schema/session changes clear or invalidate edits. A late save cannot clear newer edits or another account's draft.
- Original save, validation and error behavior is delegated unchanged. Successful complete saves clear the temporary cache; failed/rejected/additional-preference-error saves retain it.
- A short notice and Discard changes button appears only for edited fields. Discard restores the current saved/default form without saving anything; it does not undo an earlier database save or delete a customer record.
- Shell v86 updates the public HTML without forcing an open transaction to reload. No signature or consent action is performed by this batch.

## Verification checkpoint

- 16 actual-renderer runtime cases pass: late render, untouched defaults, empty/zero values, cursor/focus, successful/failed/rejected/partial saves, new edits during save, discard, identity/schema/session changes, hidden-panel focus and dropdown replacement.
- 27 focused Python tests pass, including runtime/default-save safety and startup/PWA checks.
- All 47 inline scripts parse; patch whitespace passes. Full regression, CI and actual production verification recorded at completed checkpoints below.
- Full local candidate regression: 2,525 tests in 82.277 seconds, OK (one skipped).
