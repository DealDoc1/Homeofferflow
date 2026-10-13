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
