# TXR-1508 remaining two-customer provider QA

## Scope

- Outcome: complete the still-missing two-customer showing acknowledgement review without requiring a third QA inbox, retrieving a new API key or changing real signer roles.
- Production baseline: `30cf21f132f80bb9563356e568f6d62df12844f6`. Source record `f6a80131-2454-444d-81e3-43b55ee9d96a` is already approved, attested, revision `02-25-26`; live source SHA-256 equals the original user-provided file: `b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40`.
- No new customer source-owner/brokerage-seat rule, document geometry, source activation, role grant, billing setting, customer send or real signed file change. This is an owner-only internal test, not a new gate on the existing live showing workflow.

## Fixed specimen and unsigned review

- Uses the actual released TXR-1508 renderer and field builder, not test-suite imports. Cases: two customers/broker/no other representation; two customers/associate/first represented and second not; long Unicode customer names with continuation.
- Four pages, 21 fields: the professional plus both customer initials/date rows and the three continuation initials. Only the fictional QA recipient IDs and combined page offsets/API IDs differ from the production map. Professional/customer 1 use QA A; customer 2 uses QA B. Both approved inboxes remain fixed.
- All four unsigned pages rendered and visually inspected. Names fit their own rows, compact checks fit the correct cells, blank choices remain blank, long names are complete in the exhibit and initials lines do not overlap. Original source contains one page, no AcroForm fields/widgets; generated specimen has zero widgets. The source file was not edited or committed.
- Unsigned specimen `/private/tmp/hof-txr1508-provider.jUik0T/unsigned.pdf`; manifest beside it. Field-map SHA-256 `ecdca46053742c57022595ccc7723737ca02c54571ce6f934cb40ec31e927e60` is pinned after review. No completed-provider pass is inferred from this preview.

## Delivery and status boundaries

- Existing protected operator reservation/receipt path is reused for a separate fixed showing-test scenario/revision. Request bodies accept only the exact action, never custom recipients, source IDs, fields, flags or documents. The same owner-email and platform-admin checks precede source access.
- Private source is loaded server-side from the existing published record and its bytes checked. Existing deployed credentials remain server-side; no new key, credential extraction, public source link or privilege expansion.
- Test mode is forced, invitations parallel, reminders off, no added signature page or embedded-signing authentication change. Reserve a unique run before any provider creation; timeout/ambiguous receipt never causes automatic resend. Status checks remain read-only and match document ID, test mode, name, revision and both recipients.
- Completed purchase QA now reports its already recorded placement review accurately, but a bare provider Completed status still never becomes a visual pass. Revision/source/digest evidence must match the recorded test before the pass hint appears.
- Historical draft-gate prose is explicitly marked superseded by the already released shared-library workflow.

## Local evidence

- 42 focused Python tests passed, including new fixture/operator tests and all existing purchase operator/renderer/answer-bound tests. Five real-source JavaScript UI cases passed for send/check scope isolation, exact action-only payload and disabling recorded attempts.
- Frozen full local candidate: 2,545 tests in 83.010 seconds, OK (one environment-dependent skip). All 47 inline scripts parse; patch whitespace passes. PWA shell advances to v90.
- Full candidate, exact-head CI, deliberate spend-guarded release and authenticated check/send/receipt are recorded only after completion below. Final provider-rendered initials/date/check/continuation review still remains required.

## Released and one confirmed test sent

- PR #1322 final-head CI `38348950384` passed; whitespace-only cleanup `831716c` followed the full local candidate without changing runtime behavior. Superseded CI `38348802960` was canceled intentionally. Merge `d0a5d50d4d90beb288bc5712e76205219fba3631`.
- Intentional release `38349295035` succeeded: 2,545 cloud tests in 96.119 seconds, OK (two environment-dependent skips), schema/spend check, prebuilt deployment, canonical PWA/API/packet checks. READY production `dpl_Dk5V2o3JC8iE57jPjTAiKgzNU8cy`, exact SHA and canonical aliases verified. Pre-build snapshot 2026-10-13 05:03:47 UTC: $0.03/$20 used, $19.97 unconsumed, $3 reserved; not a future billing guarantee. No previews or billing change.
- Authenticated canonical Andrew Gmail owner Admin > Showing-form signing test > Check confirmed not started. Sent once through that reviewed control; UI confirmed one nonbinding test created, parallel completion. Independent database readback confirms run `f8a7fd18-6d2c-42dd-8a07-3896ee30828d`, phase created, test_mode true, exact pinned field digest, all three cases and document `8f257940-a833-4f9e-a6e3-30359c212219`. No resend or other customer document action.
- Andrew's invitation `1a133a800d92f1d6` is INBOX, Delivered-To Andrew Gmail, 2026-10-13 05:06:50 UTC, matching exact `X-SW-Document`. Signing screen explicitly confirms Test Mode / Not Legally Binding. Six dates auto-filled; applied fictional QSA initials to this recipient's eight initials, advancing the first recipient's 14 required fields to the final step.
- The new packet's final Agree & Finish separately accepts the electronic disclosure. Requested the specific at-action decision; final acceptance remains untouched pending the human's answer. Second recipient and completed-provider PDF review remain outstanding. The test is running, not passed. Private signing URLs were not persisted in repository evidence.
- Creation screenshot `/private/tmp/hof-txr1508-provider.jUik0T/live-test-created.jpg`; final consent handoff `/private/tmp/hof-txr1508-provider.jUik0T/qa-final-disclosure.jpg`. The invitation tab was closed; only the precise signer handoff remains needed.
- Authenticated canonical Purchase > Check test status now reports Signing and placement review passed for this test for the already reviewed purchase specimen, rather than falsely requesting another review. This was a read-only check, not a new send or fabricated pass.
- Deployment error-level log sample 05:04:00-05:07:48 UTC: no matching logs. This is a bounded sample, not universal error-free evidence.
- App PR attachment failed at its existing 100-item limit; the direct PR remains available. No unrelated attachment was removed and deployment was unaffected.
