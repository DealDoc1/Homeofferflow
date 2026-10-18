# One-click offer exit

## Five batch facts

- Outcome: leave the offer interview in one click without discarding answers,
  while retaining the existing saved-draft Resume entry.
- Scope: only the nondestructive exit helper, actual-source runtime tests and
  installed-shell refresh. Existing form generation, Google address completion,
  signing recipients, enrollment, pricing and permissions are unchanged.
- Production baseline: 32ab11f9c02f015de30e7fe936efa19782ca3f23,
  READY dpl_C9CAxDShcosKDjYov6LoqYpjpF64.
- Cost: no preview, signing send, paid service, schema or credential change;
  one intentional prebuilt release after an independent capacity check.
- Proof: actual-source save/exit/Resume tests, isolated fictional browser
  interaction at desktop and phone widths, full regression, independent CI,
  exact production commit and canonical source/worker comparison.

## Implemented and focused verification

- Removed only the native confirmation in returnHomeFromWizard. Close and
  Home both use that existing helper. Exiting still schedules the guarded
  save, hides the overlay, releases modal isolation and scrolling, then
  refreshes Resume controls after the save debounce. Start New Offer still
  asks before clearing saved work.
- Actual-source Node cases cover homebuyer/agent/investor exit; fields,
  explicit zero, radio and checkbox groups, uploaded filenames, offer ID,
  owner and now-closed overlay; blank interviews; draft/account/epoch changes
  during debounce; failed device storage; wrong-account and payment-return
  Resume exclusions. Cloud calls are stubbed, not production API proof.
- Eighteen focused Python tests passed in 0.796s, including the new runtime
  harness and existing Resume, modal accessibility and autosave guards.
- Fictional-only localhost fixture uses actual production exit, snapshot,
  debounce, save and Resume-label functions with simplified interview and
  reopening scaffolding. Desktop and phone-width interactions
  returned home without a JavaScript dialog; changing the buyer's first name
  survived reopening at both widths. Cash and survey selections remained.
  The homepage was no longer inert and the Resume CTA was usable.
- The fixture does not claim the entire real interview or cold-load/cloud
  restoration was exercised. Those existing source paths are unchanged;
  existing regression tests remain in the affected test group. No live
  customer draft or packet was changed, and the user's original tab remains.
- Installed-shell v102 carries the updated helper to installed clients.
- Pending SignWell electronic-disclosure acceptance remains separate. No
  signature, provider test resend or outreach occurred in this workstream.

## Release checkpoint

Full local suite: 2,643 tests in 89.542s passed, one environment skip.
Whitespace passed. Read-only Vercel capacity workflow
38674376178 passed at 03:05:25 UTC October 15 (10:05 PM Chicago October 14):
four deployments in 24 hours, $0.04 used, $19.96 unconsumed, $3 reserved for
the September 22–October 21 cycle. This is a measured snapshot, not an account
reset or a guarantee about future usage. The production workflow repeats its
own spend check before upload.

## Deployed verification

- PR #1340 exact head 56d669f1718ddcd67e246de2ab4b9341e282ab1a passed
  independent CI 38674570237: 2,643 tests in 170.470s, two skips; golden
  rendering, signer geometry, schema preflight and whitespace passed.
  Normal merge e15c5db0138751a0232054045eda7e0b8442e465. The application PR
  attachment helper hit its existing 100-item limit; no attachments removed.
- Production workflow 38674908583 passed: 2,643 merged tests in 172.102s,
  two skips, then project/schema/spend/prebuilt/readiness/canonical/PWA and
  API/packet-runtime checks. Exactly one prebuilt deployment, no previews.
- READY dpl_47tztcZ7rgRmvVYvdCdLUubDpBSz independently matches that merge
  SHA and both canonical root/www aliases. Last pre-build credit snapshot
  03:14:44 UTC: $0.04 used, $19.96 unconsumed, $3 reserve, four prior
  deployments in the rolling 24-hour window. Not a guarantee of future spend.
- Canonical byte comparisons matched: homepage
  cd129da789a07d4d5cf4452aabf5e00bd26b833fb56a260a0da2790f59dbcd28;
  worker cafca38e481305628529bf92064a099f81485bdc8b83d353dbbc575d300c5dd1.
- A temporary canonical agent-entry tab opened the existing active account;
  closing only that account panel showed the account-aware Agent homepage
  at 390px, without reopening or changing the saved customer interview.
  Live screenshot: /private/tmp/hof-one-click-exit-live-home-2026-10-14.png.
  This confirms the released presentation, not a fresh live-customer exit
  or full signing run. Behavior proof remains the isolated actual-source
  runtime/browser tests above. Original offer/signing tabs are preserved.
- No error/fatal logs in the bounded deployment window 03:15:11–03:27:20 UTC;
  this is not a universal service-health claim. No new signatures, invitations,
  customer packet, outreach, source activation, database write or fee change.

Rollback: prior READY dpl_C9CAxDShcosKDjYov6LoqYpjpF64.
