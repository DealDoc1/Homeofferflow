# Accurate brokerage signing progress and stable account navigation

## Batch contract

- Outcome: brokerage launch progress recognizes an offer sent for signing without waiting for completion; partial signatures are not counted as completed offers. Early account navigation keeps the tab the agent chose.
- Scope: read-only administrative offer classification, the existing brokerage launch checklist, generic agent account-return routes, dashboard provider-status display, regression coverage and PWA shell v98. Preserve customer signing, simultaneous invitations, forms, Google address completion, brokerage authorization and billing.
- Production baseline: a4607d084ab381de2eed85210a4e97a6f8ada52f / READY dpl_38u4EgCWWNDiNLwXH6jqCKpXEGPR. One spend-checked intentional production deployment; automatic Git previews remain disabled.
- Completion evidence: reproduced production failure, actual-source route/checklist tests, privacy-safe payload assertions, frozen full regressions, exact-head CI, normal protected merge, canonical source comparison and settled account-tab verification.

## Reproduction and implementation

- The old Python classifier counted `Partially Signed` and `unsigned` as signed, omitted raw `completed`, and counted `Draft - not sent` as awaiting. Replaced substring checks with exact completion, progress, draft and terminal/unknown aliases. A raw provider `signed` event is one recipient's progress; legacy main offer `Signed` remains complete when no current provider status conflicts.
- Brokerage and platform API metrics share the same pure classifier. Open sent/viewed/partial offers remain awaiting completion; complete and open signing states count toward the current signing-started milestone. Drafts, unknown and terminal states do not. Current explicit provider status takes precedence over a conflicting legacy main status.
- The checklist now says "Send the first offer for signing" and uses signingStartedCount instead of signedCount. This metric covers offers, not every standalone agreement, and is not an immutable historical sent-ever ledger. Existing authorization and read-only query scopes remain unchanged. No extra database query or schema change is introduced.
- The dashboard's actual-source frontend test now also proves raw provider signed/document_signed is partial while legacy Signed remains complete. Existing separate awaiting/viewed/partial display cards are preserved.
- Actual canonical ?agent=1 reproduced the early-navigation failure: an immediate Agent Account -> Brokerage selection showed loading, then late generic account-return processing reset it to Dashboard. After a settled second click, the same real account showed active OnDemand membership. Generic routes now preserve an already-open account modal; explicit transaction and workspace links still execute their intended route.
- The signed-in owner account exposes agent membership, not brokerage-administrator controls. No role was elevated, and that agent view is not claimed as authenticated broker-admin QA.

## Read-only data and focused verification

- Privacy-safe grouped OnDemand status snapshot: 26 offers (9 expired, 9 drafts, 2 generated with no provider status, 2 awaiting signatures, 2 completed, 1 partial, 1 pending). Correct replay: 2 completed, 4 awaiting completion, 6 current signing-started offers. No buyer names, addresses, terms or document contents were retrieved for this check. This is a bounded snapshot, not a claim that records cannot change later.
- 171 focused Python tests passed across reporting, brokerage activation, tab startup, route recovery, membership isolation and affected PWA/companion tests. Another 20 focused reporting/provider-status tests passed after the frontend consistency check.
- Actual checklist runtime covers sent-but-incomplete, draft-not-sent, completed and missing metrics with preserved privacy copy. Actual route runtime covers generic open/closed account and explicit purchase links in both routing paths.
- No customer packet, email, signature, payment, subscription, partner record, database grant or account role changed in this workstream.

## Release status

- Frozen full suite, exact-head CI, merge and one intentional cost-guarded production release are pending. Canonical source/read-only account verification is pending; this file does not claim a deployment before it happens.
- Broader roadmap remains active. Completed-provider form matrices, the pending fictional TXR-1508 disclosure step, full authenticated broker-admin onboarding and additional listing-agreement implementation are separate evidence gaps.

## Frozen candidate checkpoint

- The local full suite exercised 2,615 tests in 91.739 seconds with one environment skip. Its only failure was an obsolete exact-source assertion expecting the former pending-only conditional. That test assertion was updated to include the new raw-provider-signature condition, without changing the frozen runtime behavior. The local full run is not claimed as passed; independent exact-head CI must prove the final candidate. Focused signing recovery/reporting tests are rerun after this test-only correction.

## Completed release and canonical verification

- The final focused recheck passed 30 tests. Independent exact-head CI 38561903291 passed all 2,615 tests in 102.029 seconds with two environment skips, plus approved golden rendering, standalone signer geometry, database preflight and whitespace. Candidate 20d0b17675fb42c3b0547be1a74390cba4963a09 was normally merged through PR #1333 into 4fe45d0850e7c072a16f0d9fdab0dd829e165fe4. No administrative merge bypass was used.
- One intentional release 38562344488 succeeded on that merge. Its merged full suite passed 2,615 tests in 170.061 seconds with two environment skips. Coordinated database readiness, cost checks, prebuilt artifact, canonical site, PWA and production API/packet-runtime smoke checks passed. No preview or new paid service was created.
- Fresh Vercel cost check at 2026-10-14 12:18:41 UTC reported $0.04 infrastructure credit used, $19.96 unconsumed and $3 reserved for the 2026-09-22 through 2026-10-21 period. This is a deployment-time snapshot, not a guarantee of future usage or evidence that the Vercel allowance just reset.
- READY deployment dpl_j3Yp7492NRqXJt1EM4BEHtGU57qe / homeofferflow-fgzlz4l3v-dealdoc1s-projects.vercel.app carries the exact merged revision and root/www production aliases. Canonical index.html and service-worker.js returned HTTP 200 and matched the reviewed source byte-for-byte. SHA-256: index 7b502f5cd7f639db8278c18156e2adaf97761f5678579b7c629a9ca9d9dc7400; worker e6ad397aa15fa3c3eac702d5db058ad8406f0d782771e250120389f32e7e8cab.
- Actual canonical ?agent=1 -> immediate Agent Account -> Brokerage initially showed Loading brokerage workspace, then settled to active OnDemand membership without resetting the selected tab. The account modal remained open, Brokerage remained active, dashboard loading was finished and the generic route marker was cleaned. Phone display at 390x844 was visually reviewed with page width exactly 390px. The temporary viewport was reset and the existing site tab retained as the result; existing SignWell handoff tabs were preserved. No extra Chrome tabs were opened.
- A fresh privacy-safe aggregate read returned the same 26-offer distribution before release. Reporting replay and safe broker payload tests prove 2 completed / 4 awaiting completion / 6 currently started; no authenticated broker-admin live API/UI count claim is made because this real session has agent, not broker-admin, access.
- Deployment-scoped error/fatal log sample from 12:18:53.719 through 12:21:06.734 UTC returned no matching records. It is a bounded smoke sample, not continuous monitoring or proof of every broader roadmap workflow.
- This bounded workstream is deployed and production-verified for account navigation and source/runtime identity. The overall roadmap remains active; pending provider completion and full authenticated brokerage onboarding are not falsely marked complete. No customer packets, emails, billing, subscription, role or database write occurred.
