# Customer workspace language

## Scope and baseline

- Outcome: concise professional brokerage and guided-document wording, without changing transaction data, forms, access, pricing, signatures or Google address completion.
- Baseline production `d0a5d50d4d90beb288bc5712e76205219fba3631`. This batch is independent of the already sent nonbinding TXR-1508 test; its final consent/completed-provider review remains pending, and no test is resent here.
- Extend the existing document-language helper rather than adding a competing layer. No backend/database/API change, role grant, profile save or customer packet mutation.

## Changes and reproduction

- Removed the redundant not-editable-from-the-browser paragraph from the connected brokerage card. Keep brokerage identity and current membership clear.
- Replace privacy-limited/operational jargon with team activity, preserving the explicit client/transaction privacy statement. Team labels still do not change access or plans. Pending brokerage membership copy explicitly preserves individual workspace/shared-form access; activation controls and authorization remain unchanged.
- Guided prompts use Answer the questions instead of source/revision scaffolding, and Choose a payment plan instead of Choose the printed plan. Underlying option values, required acknowledgements and professional-review cautions remain unchanged.
- Actual-source runtime tests reproduced three failures: missing plain-language transformations, unclear plan prompt and a text-normalizer fixture rewriting user textarea text. The last is a reproducible unsafe traversal, not a claim that a real client record was corrupted.
- Skip text inside user controls/contenteditable when normalizing help text. Skip action buttons within status text; preserve their nodes/handlers. Only the empty prompt option is renamed, never a selected/stored value.

## Verification

- Five actual-source JavaScript runtime cases pass: clear help text, prompt/value preservation, required checked acknowledgement preserved, entered textarea text untouched and Review and send handler intact.
- Thirteen focused Python tests passed, including all preserved historical customer-language tests, brokerage-load isolation and membership recovery. No pre-existing test cases were removed.
- PWA shell advances to v91. Full regression, exact-head CI, spend-guarded release and canonical brokerage/guided-form visual checks are recorded after actual completion below. This is not a claim that all four intake paths or all broker-admin operations were newly tested.
- Final focused set: 90 Python tests passed. The first full run found two old exact-copy expectations; updated their wording while preserving all authorization/privacy/availability checks, without changing runtime behavior. Frozen final full candidate: 2,550 tests in 81.952 seconds, OK (one environment-dependent skip). All 47 inline scripts parse; staged patch whitespace passes.

## Released checkpoint and actual UI boundary

- PR #1323 exact-head CI `38352812886` passed; merged as `e8e71164f8d6113a2a179763b8d17539e52b63be`. App attachment failed at its existing 100-item limit; direct PR still available.
- Intentional release `38353191823` succeeded: 2,550 cloud tests in 137.690 seconds, OK (two environment-dependent skips), schema/spend guard, prebuilt deploy and canonical PWA/API/packet checks. READY `dpl_21BcEvz68q7KGQLEMPrkp64kGjta`. Pre-build snapshot 05:50:32 UTC: $0.03/$20 used, $19.97 unconsumed, $3 reserve; not a future billing guarantee.
- Actual canonical agent Brokerage now shows just OnDemand Realty and active membership, without the redundant browser/programming paragraph. Screenshot `/private/tmp/hof-customer-brokerage-copy.jpg`. Guided Forms cards now use Answer the questions wording and retain the appropriate credit/value/professional-review cautions.
- This live check also found the older normalization lowering Review at the start of a sentence in two lease-card descriptions. It is corrected separately in `document-review-sentence-case-2026-10-13.md`; no full guided-copy pass is claimed before that check is finished.
