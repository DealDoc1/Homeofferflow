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
  reopening scaffolding. Desktop 1280x900 and phone 390x844 interactions
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

Full local suite: 2,643 tests passed, one environment skip (see local regression
log for elapsed time). Whitespace passed. Read-only Vercel capacity workflow
38674376178 passed at 03:05:25 UTC October 15 (10:05 PM Chicago October 14):
four deployments in 24 hours, $0.04 used, $19.96 unconsumed, $3 reserved for
the September 22–October 21 cycle. This is a measured snapshot, not an account
reset or a guarantee about future usage. The production workflow repeats its
own spend check before upload.

CI and deployment identities are recorded only after completion. Until then
this is locally tested, not a deployed or completed-provider signing claim.

Rollback: prior READY dpl_C9CAxDShcosKDjYov6LoqYpjpF64.
