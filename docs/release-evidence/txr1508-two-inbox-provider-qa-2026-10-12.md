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
