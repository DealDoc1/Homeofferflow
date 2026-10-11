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

## First controlled attempt and credential diagnosis

- PR #1307 passed independent run `38154326122` and merged as `6a4963a`; no Vercel deployment was requested.
- Controlled attempt `38154670719` matched the reviewed layout and existing project, found an existing configured credential, and saved the attempt metadata before calling SignWell.
- SignWell returned HTTP 401. The safe receipt records authentication rejection and no confirmed document ID; no resend was performed. The authenticated Documents list remained at 142 records and did not show the requested release-tagged test.
- The original environment parser did not decode Vercel's quoted control-character serialization. Correct the QA reader, and add an explicitly read-only `AUTH_CHECK` mode that looks up the existing nonbinding QA document `0093c1e0-8491-4a14-b659-dda35a8fbed4`.
- Compare legacy and properly decoded credential handling inside the protected runner. Export only lengths, control-character flags, response codes, and confirmation of the known QA record. Do not export keys, response bodies, signer links, or environment files; do not create a new credential or change live configuration.
- Credential diagnosis cannot send a document or reserve a new send attempt. Production credential health is not yet inferred from the failed QA reader; wait for the read-only result before claiming a live authentication problem.

## Read-only result and protected-credential boundary

- PR #1308 passed independent CI `38156418880` and merged as `85bf19fb007530593bb1d5763562f6921574f4bf`. Its local regression ran 2,495 tests successfully with one skipped; no customer code or Vercel deployment changed.
- Read-only run `38156897506` completed successfully as a diagnostic. Both credential candidates returned HTTP 401; decoding did not change them, and neither trailing whitespace nor transport control characters were present. This disproves the escaped-newline hypothesis for this runner.
- Read-only Vercel environment metadata confirms `SIGNWELL_API_KEY` is a Production Secret (`type: sensitive`, `visibility: secret`, `decrypted: false`). Vercel does not export Production Secrets in an environment pull. The diagnostic therefore does not establish the validity of the credential actually injected into the production runtime.
- Remove the production environment-pull fallback from this QA workflow. Require an already configured runner credential before dependency installation, specimen generation, attempt reservation, or provider calls. Do not create a key, copy a production Secret into GitHub, change its visibility, or bypass the recorded attempt.
- Reject redaction/masking placeholders before a provider lookup. Missing runner credentials are a QA execution limitation, not evidence of a customer-signing outage or a new agent access requirement.
- Fresh completed-provider PDF inspection still needs an authenticated QA execution path using the actual reviewed generator map. Manually placing different fields in a provider editor would not validate that map. No additional test or client packet was sent during this correction.
- Boundary correction verification: sixteen focused tests pass; full local regression ran 2,497 tests in 97.893 seconds, OK with one skipped. Patch whitespace passes. This is QA-only source, not a customer release.
- PR #1309 passed independent CI `38174437459` and merged as `ef843a9db37e1b3cdf76ff5ca2fa74d8e0ab0604`; no standalone Vercel deployment or test send followed.
- Subsequent authenticated production Admin > Check delivery connections reported SignWell ready and Resend ready, without creating a document or sending email. Actual runtime connectivity is verified. The remaining gap is fresh provider-completed geometry inspection via an authenticated QA path, not a proven production credential failure.
