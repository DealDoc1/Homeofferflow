# Account startup tab stability

## Batch contract

- Outcome: keep the tab an agent selected while profile/subscription/offer data loads; do not unexpectedly return to Dashboard.
- Scope: account-opening presentation, selected-tab intent, obsolete startup requests and recovery presentation. No server authorization, source, signature map, legal consent, pricing, schema or SQL write changes.
- Production baseline `b13dac13e410b9a615b4ec174a131790e9f1bc8a`, READY `dpl_CCLtZoVEoqo5rdR6iRYC4P23CM67`.
- Cost: focused local checks, one final local suite, independent CI and one guarded prebuilt release. No previews, signing sends or customer transaction edits.
- Evidence: actual delayed-loader navigation matrix plus authenticated canonical selected-tab retention after release.

## Cause and correction

- Observed on the canonical owner account during PR #1316 verification: Admin was selected while the account opened, then the visible panel returned to Dashboard when startup finished; keyboard focus remained on Admin.
- The original `openAccountDashboard()` always called `showAccountTab(opts.tab || 'dashboard')` after all four remote loads. That older entry point overrode newer navigation intent.
- Track tab-selection revision and startup revision in the existing account shell. A selection during loading, including deliberately clicking Dashboard again, takes precedence over the original shortcut.
- The latest startup request, signed-in user identity, profile-session epoch and open-modal state must still match before startup continues or renders. Older/closed/different-account starts cannot route the view or clear a newer loading state.
- Default Dashboard/transaction chooser and explicit shortcuts remain unchanged when there is no later tab selection. Existing error/retry card is preserved without forcing a tab jump.
- This is client presentation lifecycle only. It does not make authorization decisions from user metadata, change credentials, grant access or modify any user data.
- Shell v85 refreshes the customer HTML without forcing an open transaction to reload.

## Regression

- New actual-source runtime matrix: 11 cases. Nine failed before the correction; all 11 pass after.
- Covers Profile, My Offers, Brokerage, Guided Forms, Admin, default/explicit shortcuts, deliberate Dashboard selection, load failure, overlapping starts, closing and account change.
- 81 focused Python checks pass, including the runtime matrix, account loading resilience, activation/dashboard, modal accessibility and PWA cache checks.
- All 46 inline scripts parse; patch whitespace passes. Full regression and live outcome recorded at their completed checkpoints.
- Full local candidate regression: 2,523 tests in 81.621 seconds, OK (one skipped).
- The separate prepared nonbinding SignWell QA consent tab is not submitted or changed by this batch. No final signing/PDF pass is inferred from this UX fix.
