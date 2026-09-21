# Scope autosave to the intended offer

Status: locally implemented and tested; not deployed or browser-verified.

## Customer and cost outcome

- Offer autosave handlers now ignore input/change events outside the offer
  interview. Editing profile, partner, or admin fields no longer schedules an
  offer snapshot replacement or an unrelated cloud save from those handlers.
- A delayed save retains its original draft object, user ID, and sign-in
  generation. Switching offers/accounts or signing out and back in discards
  that obsolete save. A normal same-account token refresh remains supported.
- An offline notification on an inactive page no longer writes a draft.
  Actual account-offer edits saved offline retain a single in-memory sync
  reference. Reconnection syncs only that still-current draft/account/sign-in.
  Closing the interview does not discard valid pending offline work.
- Existing edit debouncing, deliberate save-on-close, active beforeunload
  saving, and local-only homebuyer drafts remain supported.

These changes reduce unnecessary save invocations in the covered flows; no
production request reduction, billing savings, or conversion lift measured.
The offline sync reference is not a new durable queue or background service.

## Verification

Baseline: `26b4eebe`.

- New runtime suite: 26 passing cases executing the actual event handlers,
  save scheduling, local saver, and connection-status functions with mocked
  timers, storage, DOM, and cloud invocation boundaries.
- Against the baseline: 15 failures reproduced; 11 positive controls passed.
- Covers outside-form edits, input/change helpers, rapid edits, offer/account
  changes, sign-out/re-sign-in, token refresh, restoration suppression, explicit
  close saving, offline active/inactive behavior, matching offline recovery,
  obsolete offline recovery, beforeunload, and homebuyer local-only saves.
- Final full suite: 1,998 passed in 16.625 seconds. Printed invalid-fixture PDF
  and preflight rejection diagnostics are expected negative-test output, not
  new production failures or live release checks.
- All 45 inline scripts parse; `git diff --check` passes.

## Release limits

No authenticated browser, live database, or production verification performed.
No customer messages, signatures, payments, documents, or external settings
changed. No GitHub publication or Vercel build/preview/deployment started.
No new dependency or recurring service cost. Record in the daily report as
locally tested and awaiting release, not deployed.
