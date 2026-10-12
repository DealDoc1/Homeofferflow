# TREC 39-11 static PDF cleanup and guided source-load recovery

## User outcome and release boundary

- Agents can open the existing amendment interview, prepare the selected contract changes, and review a clean signing-copy PDF.
- Scope: TREC 39-11 / trec 39 11 renderer, its traceable admin render revision, the amendment guided opener, focused tests, and installed shell v83.
- Prior verified canonical production: `0109881c426a8328225bd58d9b2c18b3c1cfa67c`, READY `dpl_3n8uXBf7obNbZaaPmfTdgNTzgHtq`.
- One coherent intentional prebuilt release, no previews; preserve the existing live budget/reserve check. Previous report-only evidence is included without a separate deployment.

## Approved source, authorization, and signing plan

- Approved source: existing official TREC 39-11, printed revision 05-04-2026. Exact source fixture SHA-256 `d12909bcbd014080948eb6f9771231ba1b1d98c64eaf07e87ab0faa1118b8d36`.
- Current production source-vault metadata is approved for TREC-39-11 at that revision. Source PDF, private vault object, authorization, and printed terms are unchanged.
- Release authority: standing owner direction to correct workflow defects and deploy completed enhancements without repeated approval. No new source-owner, agent-attestation, brokerage-seat, credential, or permission requirement is added.
- Signing plan remains one or two Buyers plus one or two Sellers, parallel invitations, existing signature rectangles, and each party's continuation initials. No recipient, field type, required flag, date, or coordinate changes.

## Reproduced defects and corrections

- Official source has 54 canonical field entries and 51 Widget annotations. The previous generated PDF retained all 51 Widgets but had zero canonical fields, producing viewer warnings and orphan editable elements.
- Generated copies already paint the selected interview answers and use SignWell's separate signing map. Remove only original Widgets from those copies and omit any residual AcroForm tree. Preserve source bytes and non-widget links. Do not flatten or edit any signed customer PDF.
- Synchronize the admin snapshot with renderer `trec-39-11-2026-10-11-static-source-v2` so later provider evidence identifies the actual generator.
- Authenticated QA: the normal guided Purchase > another purchase document > amendment path opened successfully after the source loaded. The earlier transient "Opening" symptom was not reproduced as a persistent failure.
- Fault injection reproduced a separate concrete error: the amendment opener swallowed a failed source lookup and fulfilled its promise. The guided handoff then removed its loading/error state as if opening succeeded. Propagate that rejection to the existing retry handler; do not add another gate or duplicate message.

## Verification

- One combined unsigned review specimen covers ordinary four-party terms, one Buyer/one Seller option waiver, and long Unicode continuation: four pages, all visually inspected.
- Before/after PNG hashes match exactly on every page. Printed source graphics, checkboxes, entered answers, and continuation text are unchanged. Poppler warnings decreased from nine to zero.
- Before/after signer manifests match byte-for-byte. Source hash is unchanged, generated copies have zero Widgets and no AcroForm, and a deliberate non-widget link survives.
- One hundred affected parser/renderer/opener/PWA/agent-handoff tests pass. The fault test executes the actual amendment asset and guided handoff helper and confirms a failed source retains Try again without reporting a successful opening.
- Standalone TXR signing geometry baseline passes. Full local regression, independent CI, and canonical deployment are recorded at their completed checkpoints.
- Final local regression: 2,506 tests in 84.873 seconds, OK with one skipped. Patch whitespace passes. No production database migration or configuration change is required.
- Authenticated production verification after release will use one plainly labeled synthetic draft, inspect persisted values, and download only its unsigned preview. No client packet, provider document, email, or signature send is authorized by this QA step.
- Rendered signed-PDF QA / completed signature visual QA for the new amendment workflow remains unverified. This structure-only cleanup and unchanged-map comparison do not claim completed-provider inspection.

## Deployed and authenticated end-to-end verification

- PR #1312 passed independent CI `38177585826` and merged as `ee90d4d627b6ffd85bff673a4c52ab2a501ee6c8`. Superseded CI `38177551791` was canceled after the documentation-only evidence label changed; it is not the final check.
- Intentional release `38177868605` succeeded: 2,506-test regression, whitespace, release preflight, schema readiness, spend safety, prebuilt build/deploy, canonical, PWA, and packet-runtime checks passed.
- READY production `dpl_FwBNH37LDFErdd1HQ9StV5oWGUz7`, `homeofferflow-jgc1qxbie-dealdoc1s-projects.vercel.app`, exact merge SHA above. Both canonical aliases point to it. Canonical amendment asset hash matches the released file; live worker is v83.
- Live pre-build spending snapshot: $0.03 consumed, $19.97 unconsumed of the $20 infrastructure credit, $3 reserved. One actual Vercel deployment for this batch; no previews.
- Authenticated owner followed Purchase > another purchase document > amendment on the released site. Google-enabled address input remained present. Created exactly one plainly labeled QA-only draft with one fictional Buyer, one fictional Seller, and a closing-date change to December 1, 2026.
- Draft ID `b7a72cce-af2a-4bbc-b71c-101e735b6b9a`; persisted source revision 05-04-2026, closing date 12/01/2026, selected change closing_date, and intended QA parties match the UI. Status remains draft; provider document ID, sent_at, and signed_at remain null.
- Review and send opened the prepared-document list. Only this draft's Preview was selected; Send for signature was never selected. Downloaded unsigned preview has one page, zero canonical fields, zero Widgets, no AcroForm, the correct QA marker and closing date, and the correct TREC 39-11 source footer. The actual production PDF was visually inspected and rendered without warnings.
- Saved browser screenshot shows the live draft-ready state. The download helper took roughly 28 minutes despite its requested short timeout; this is not a measured API response delay. Future download checks should use the visible Download control plus bounded file verification rather than repeating that long helper wait.
- Updated the existing additional-texas-forms roadmap record to this release and the actual remaining provider review. Its status stays in_progress and QA partial; no false completion is recorded. Read-back confirms the update.
- No real client packet, source PDF, or signed agreement was edited, sent, or signed. No email, SignWell request, new credential, permission, or production migration was created.
