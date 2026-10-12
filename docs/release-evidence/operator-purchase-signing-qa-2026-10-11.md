# Protected operator purchase signing check

## Batch contract

- Outcome: submit the already reviewed synthetic purchase specimen through the actual production SignWell runtime, without exporting a protected credential.
- Scope: owner-only Admin delivery-tools action; fixed QA specimen library shared with the local helper; existing QA tracker records. No customer signing settings, sources, placement maps, billing counts, brokerage access, or customer agreements change.
- Production baseline: `ee90d4d627b6ffd85bff673a4c52ab2a501ee6c8`, READY `dpl_FwBNH37LDFErdd1HQ9StV5oWGUz7`.
- Cost: no previews; one intentional prebuilt deployment; exactly one provider test attempt for this reviewed map revision. Test mode is nonbinding and excluded from SignWell API billing per https://developers.signwell.com/reference/createdocument.
- Completion evidence: replay/security tests, exact reviewed layout identity, regression and independent CI, canonical owner action, persistent safe provider receipt. Completed signatures and final provider PDF inspection are separate remaining evidence until actually available.

## Implementation and safety

- Two fixed recipients: `andrewchri@gmail.com` and `brewbqinfo@gmail.com`; simultaneous invitations, no reminders or added signature page.
- Only existing verified owner accounts plus existing platform-admin authority can invoke the action. Request bodies accept only the action name, never custom recipients, source records, PDFs, fields, live/test mode, or release identifiers.
- The existing deployed signing credential remains inside the server. No new key, changed environment variable, credential export, or protection change.
- Server specimen has no imports from tests/scripts. It uses the same production generator and map as the previously reviewed helper. Source checksum, renderer revision, page/field counts and exact field digest are pinned.
- Thirteen pages, 26 fields, three cases: one Buyer, four-party execution, long Unicode contact continuation. Only the already reviewed pages are copied; signer IDs and assembled page numbers are remapped, not geometry.
- Layout fingerprint remains exactly `f9f006620d97dccce36b273f52544788d7c664e453b199d98e74e694d9cbaf34`, matching the prior all-page visual review. No new overlay or changed production PDF is introduced.
- Existing `hof_qa_runs` unique `(scenario_id, release_name, environment)` reserves the attempt before provider POST. A repeat, concurrent loser, timeout or uncertain response cannot create another document. The fixed QA revision does not change with unrelated deploys.
- The scenario is a bounded data record, not a schema migration. Existing server-only tracker access and constraints remain unchanged. No grants, policies, sources or customer rows are modified.
- Only safe receipt metadata persists. Provider bodies, exception text, credential values and signer URLs are not logged or exported. A failed final receipt write preserves the prior reservation and returns the known document ID for manual inspection; no automatic retry.
- Check test status is read-only. It validates document ID, test mode, QA name/revision, and the exact two recipient addresses before interpreting provider status. Provider completion never marks final visual QA passed.
- Existing failed runner attempt and its HTTP 401 receipt are preserved. This fixes the execution boundary; it does not treat an ambiguous attempt as safe to replay or create an agent-facing gate.
- Shell v84 refreshes the deployed owner interface without interrupting an open transaction.

## Verification checkpoint

- Focused checks: 44 tests passed (owner/admin boundary, fixed recipients/nonbinding settings, reservation before send, concurrent loser, timeout, failed persistence, redaction, read-only status, layout identity, existing helper and connection health).
- All 46 inline page scripts parse successfully. Patch whitespace passes.
- Full candidate regression: 2,519 tests in 84.461 seconds, OK (one skipped).
- Local regression, independent CI and actual production receipt: record at their verified checkpoints below.
- No test email or new provider document has been created at the implementation checkpoint. No signed client document has been changed.

## Independent CI and pre-deploy correction

- PR #1313 passed independent run `38197900775` (regression, golden rendering, standalone geometry, schema preflight) and merged as `c436aef4365a3d2381c98d7760ca617ebb6c93a0`.
- Release run `38198137957` passed its regression but stopped at committed-range whitespace validation: one blank line at the end of the new test file. No Vercel build, deployment or provider send occurred.
- Remove only that trailing blank line; no customer code, map, source, behavior or test assertion changes. Check whitespace against the actual release baseline before the retry. The local full-candidate regression remains applicable to the identical executable content.
