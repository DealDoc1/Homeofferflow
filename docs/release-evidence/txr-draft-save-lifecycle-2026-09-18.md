# TXR draft-save lifecycle repair — September 18, 2026

Status: locally implemented, runtime-tested, and browser-tested with simulated
responses. Not pushed, deployed, or production-verified.

## Scope and cause

An agent completes the TXR-1919 loan-assumption or TXR-1917 environmental
interview, saves the private draft, and opens the existing review/signing queue.
Both submit handlers dereferenced `event.currentTarget` after awaiting the
save response. Browser dispatch has ended at that point, so the reference is
null. The save could succeed while the UI caught its own subsequent exception
and displayed an error instead of the review action. The buttons also remained
available while the request was pending.

The handlers now capture the submit control synchronously, reject repeated
submissions while it is disabled, show a saving state with `aria-busy`, and
retain the successful Review and send action. Success leaves the save control
disabled and labeled Draft ready. Rejection/network errors restore its original
label and availability, retain the entered values, and do not automatically
retry. Status messages are exposed as polite live status updates.

No form terms, source mappings, payload fields, backend actions, authorization,
database schema, recipient selection, or signing behavior were changed. The
UI guard prevents repeat submissions in that open form; it is not a claim of
server-side idempotency across tabs or an ambiguous network failure.

## Verification

- `node --test tests/txr_draft_submission.runtime.cjs`: **10 passed**. The tests
  execute both complete production script blocks with deferred fetch responses,
  clear currentTarget immediately after dispatch, and cover success, pending
  and post-success duplicate attempts, validation retry, network failure, and
  review handoff without a signature-send request. Against unchanged source,
  all ten checks failed: success/review checks saw an error, duplicate checks
  observed two requests, and retry/network checks lacked the busy-state reset.
- Full Python discovery: **2,110 tests in 35.415 seconds; 2,108 passed**.
  Only the existing `test_every_current_map_matches_the_source_calibrated_baseline`
  and `test_current_released_maps_match_the_approved_baseline` failures remain.
  TXR-1507 approved-map fixtures remain unchanged pending final provider QA.
- `git diff --check`: clean.

The reusable `scripts/qa/txr_draft_save_preview.cjs` serves only a loopback test
page, with the actual two interview scripts and synthetic identity/source/API
responses. External connections and form navigation are blocked by CSP; no
customer data or production credentials are loaded. Browser evidence:

1. Both form cards and the actual interview controls rendered.
2. TXR-1919 native form submission showed one pending request and a disabled
   Saving draft button. Releasing the simulated response showed the ready
   status and Review and send action, not a late form-reference error.
3. That action closed the form and opened the simulated review queue without
   making another request.
4. TXR-1917 simulated validation failure retained all entered answers and
   re-enabled Save private draft. A deliberate retry succeeded and reached
   the same review handoff. Across this sequence there were exactly three
   simulated save requests and two review opens.

The browser logged one initial "Could not establish connection. Receiving end
does not exist." message. Its origin was not established; it did not recur
during the interactions. No form-handler exception was observed. This is not
a completely clean-console claim.

The fixture verifies the native DOM/async UI boundary, not real authentication,
backend persistence, complete production layout, generated PDFs, or provider
signature delivery. No actual draft or signature request was created.

## Live roadmap reconciliation context

A read-only Supabase query on September 18 confirmed TXR-1919 and TXR-1917
remain `in_progress` / `partial`, with separate draft/review/send workflows
rather than combined-purchase-packet integration. This repair improves those
existing workflows; it does not close their entire roadmap scope. Other
entries still include form-signature QA, branding QA, natural-resource lease
support, and state expansion. The hydrostatic tracker still describes the
foundation even though the interview/combined-packet implementation exists
locally in the September 15 evidence. Local progress is not production status.
No production tracker row was modified. Preserve the release/cost hold and
report implemented, browser-tested, and deployed work separately.
