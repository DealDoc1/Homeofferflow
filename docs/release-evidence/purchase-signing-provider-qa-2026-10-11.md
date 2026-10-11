# Controlled purchase-contract provider placement check

## Outcome and scope

Close the fresh completed-provider verification gap for the deployed purchase-contract contact and execution correction. This is an operator QA helper, not a customer flow or new signing-access requirement.

- Verified production: `da511a0d242d3026e7b716ad6cfbfeea3c4c49a5`, READY `dpl_96vs29Ewd4sSrezwrTQ7nRuYEHnS`.
- Generator, sources, customer UI, pricing, and production signing settings are unchanged. No Vercel build or deployment is required for this QA-only workflow.
- Use only the existing two approved QA inboxes; no real client packet or identity is reused.

## Reviewed specimen and signing plan

- Thirteen pages; 26 fields; one combined nonbinding provider document.
- Single Buyer: source pages 1, 8, 10, 11; four signing fields.
- Four-party execution: the same four source pages with the existing two-Buyer/two-Seller execution map; twelve signing fields. Unchanged temporary-lease pages are not included.
- Long Unicode contacts: the same four source pages plus the contact continuation; ten signing fields.
- Source pages are copied unchanged from the actual production generator. Only assembled page numbers, unique case-prefixed field IDs, and recipient IDs are remapped for the two QA signers. Geometry, field types, required flags, locked dates, and date format remain intact.
- Every copied content stream is checked byte-for-byte against its generated source page. The reviewed layout fingerprint also includes every visible glyph's position/font/size and every signing box. This avoids treating harmless PDF object-number differences as a changed layout.
- All thirteen final unsigned pages were visually reviewed. A QA-only extra label overlay was removed after visual review caught page-rendering distortion; it is not present in the submitted specimen. Provider test mode supplies the nonbinding marking.
- Reviewed layout SHA-256: `f9f006620d97dccce36b273f52544788d7c664e453b199d98e74e694d9cbaf34`.

## Send safety and cost controls

- Explicit manual `QA_ONLY` dispatch on protected main; no automatic sends, cron, or customer button.
- `test_mode: true`, `apply_signing_order: false`, `with_signature_page: false`, and reminders disabled. SignWell documents that test-mode requests are nonbinding and excluded from API billing: https://developers.signwell.com/reference/createdocument.
- Reuse an existing credential inside the protected runner; never log its value, publish environment files, create a replacement key, change variable protection, or change live signing mode.
- Pin official action revisions and the existing Vercel CLI version. Check the actual existing team/project before using its configuration; do not request a deployment.
- Require unchanged production-generator source and the exact reviewed layout fingerprint before any send.
- Reserve a persistent metadata-only attempt artifact before the provider call. Reject another attempt for the same release while that record exists. Save a safe receipt, and do not retry an ambiguous provider response.
- Signing links and provider response bodies are never exported. The unsigned synthetic specimen has seven-day retention; small attempt/receipt records have ninety-day retention.

## Verification boundary

- Ten QA-helper/workflow tests and six source-alignment tests pass locally.
- Full local regression: 2,491 tests passed with one skipped. Protected CI and the actual test submission are recorded at their completed checkpoints.
- Preparing or submitting a test is not inbox-delivery proof, completed signing, or final provider-PDF inspection. Those remain unverified until their actual evidence is available.
