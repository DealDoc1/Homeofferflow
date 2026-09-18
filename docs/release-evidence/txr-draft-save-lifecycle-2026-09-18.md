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

## Full interview save-state audit — September 18 follow-up

Extended the same runtime checks across all eleven existing TXR interviews:
1501, 1506, 1507, 1508, 1905, 1914, 1917, 1919, 1948, 1953, and 1954.
This executes each complete interview script, opens its form, and exercises
its actual submit callback. It does not merely search for guard strings.

The pre-change matrix passed 34 of 55 checks and failed 21:

- TXR-1914 left its save button available during the request and did not guard
  repeat handler invocations. TXR-1948/1953/1954 disabled their visible button
  but lacked an in-handler guard against another submission. All four now
  guard pending/success states, show a busy state, and restore the exact prior
  label after failure. Status messages are exposed as polite live updates.
- TXR-1501/1506/1507/1508/1905 already prevented repeat saves, but successful
  responses left their controls labeled Preparing/Saving with aria-busy true.
  They now clear the busy state and display Draft ready after success.
- The two previously repaired forms remain passing without further changes.

Final runtime matrix: **55 passed**. For every form it checks success after
currentTarget clears, repeat submissions during and after saving, explicit
retry with identical answers after validation failure, network-error recovery
without an automatic retry, and opening the existing review queue without
sending a signature request. Successful controls must be disabled, no longer
busy, and labeled Draft ready.

Full suite: **2,110 tests in 35.360 seconds; 2,108 passed**, with only the same
two outstanding TXR-1507 approved-map comparison failures. The final added
label assertion was also rerun across the complete 55-check runtime matrix.
No payload terms, PDF coordinates, authorization rules, or signing settings
changed. No new browser test is claimed for the nine follow-up forms; the
earlier browser pass covers TXR-1917/1919 only. This is local save-flow QA,
not all-form legal-content, persistence, or completed-signature verification.

The exact TXR-1507 candidate test was rechecked read-only in authenticated
SignWell during this follow-up and still showed In Progress with the
associate signature/date placeholders. No reminder or replacement was sent.
No Git push, deployment, production write, or paid resource was used.
