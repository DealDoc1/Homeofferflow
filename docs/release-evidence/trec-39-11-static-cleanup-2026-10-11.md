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
