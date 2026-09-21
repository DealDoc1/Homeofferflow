# Attachment upload isolation — September 18, 2026

## Implemented locally

- Bind delayed PDF reads to their original offer object, account identity, and account epoch.
- Discard stale successes and failures after an offer/account change or explicit reset.
- Serialize rapid file selections so later selections do not overwrite earlier ones.
- Preserve removals, ordering changes, and document labels made during a file read.
- Keep file-count and byte limits across queued selections; prevent packet submission while files are still being added.
- Clear the file input and busy state on reset without letting old completions clear a newer upload's busy state.

No signature fields, recipient identities, legal terms, source PDFs, or provider settings changed.

## Verification

- 17 actual-function Node runtime scenarios pass, covering delayed header/body reads, offer/account/signout/epoch/reset changes, token refresh, overlapping selections, removals/reordering, count/byte limits, submission timing, and stale read rejection.
- Four selected scenarios fail against baseline `c4d6ff7f` for the expected behavioral reasons: cross-offer attachment, out-of-order completion, resurrected removed files, and submission before upload completion.
- Full local suite: 2,031 tests pass in 17.399 seconds.
- All 45 inline JavaScript blocks parse; `git diff --check` passes.
- Synthetic files only. No customer documents uploaded or sent. No browser end-to-end or production verification claimed.

## Daily reporting boundary

For September 17 08:00 through September 18 08:00 America/Chicago:

- No local commits fall within that reporting window; no verified production deployment is recorded.
- Simultaneous-signing verification: 30 relevant local tests passed; change remains unreleased.
- PR #1227 was checked live September 18: OPEN, not merged, head `a2a5b8a0e0d83c711065c5ae7398c78daa9d34ac`; Python CI last passed September 15 at 16:10:05 UTC. This is not a new CI result for the reporting window.
- The upload fix completion and full suite above occurred after the September 18 reporting cutoff and belong to the next report.
- No measured production UX or revenue impact from these local-only changes.

## Release state

Local only. No push, preview, Vercel build/deployment, payment, email, or production data mutation. Existing publication restrictions and cost hold remain in place; no current quota or spend amount was inferred from older figures. Production integration and browser verification remain outstanding, including a fresh simultaneous signing invitation check after release.
