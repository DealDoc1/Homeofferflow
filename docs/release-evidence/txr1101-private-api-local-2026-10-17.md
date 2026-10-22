# TXR-1101 private API integration - October 17, 2026

Later local interview/queue work, current durable checkout and workstation
recovery are recorded in [the mobile interview checkpoint](txr1101-mobile-interview-local-2026-10-17.md).
The status below describes this earlier API slice, not a production release.

## Batch contract and current state

- Intended outcome: the guided sale-listing interview can save/edit the same
  private agreement, preview the actual source and review recipients before
  using the existing tracked SignWell delivery flow.
- Scope: existing admin API, source activation metadata, coordinated database
  allowlist/readiness migration and focused tests. No parallel signing funnel.
- Last verified production: 7b408eb09b46720261e8fed4712fe42e81547f33,
  release 39028545771. **These changes are local, not deployed.**
- Cost constraint: local tests, no preview, no Vercel build/deploy, no real
  signing invitation, source upload, production DDL or billing mutation.
- Completion evidence remains the interview/queue integration, private source
  registration, completed-provider PDF QA, frozen full regression and one
  coordinated spend-protected release with live schema/readback verification.

## Implemented locally

- `create_txr_1101_draft` parses explicit source-specific answers and gets the
  acting identity from the verified session. Browser-supplied owner/organization
  fields cannot select ownership. The shared source host remains audit data,
  not the agent's brokerage identity or a seat requirement.
- Exact save readback validates owner, form, source, parties and answers.
  Unconfirmed saves return HTTP 409 with `refreshRequired`, directing the
  caller to saved documents instead of blindly creating another copy.
- `update_txr_1101_draft` edits the same unsent owned record using its saved
  `updatedAt`. Conditional writes reject another window's update, wrong owner,
  sent/void records and any existing provider document. Empty/mismatched write
  responses cannot claim success. Equivalent database timestamp formatting is
  compared by instant, not raw string, on the successful write readback.
- Only these two listing actions receive a bounded 128 KB answer envelope for
  long Unicode details. Other actions retain the existing 12 KB limit; private
  source upload retains its separate size limit.
- Existing private-preview, recipient-review, send, status/download and durable
  delivery paths dispatch to TXR-1101. Bookkeeping is separated from legal
  answers without silently dropping unknown answer keys. Source approval and
  exact revision are rechecked, and the renderer enforces actual source bytes.
- Seller labels and saved notice emails populate recipient review. The actor's
  associate identity or the explicitly selected broker is separate. Identical
  legal names do not silently merge two sellers; confirmed signing emails
  must still be distinct. No signing order is introduced.
- Listing-only context includes the active agent-linked office's saved address,
  phone and email, never the source-host's contact details. Existing forms keep
  their prior context shape/fingerprints. Independent agents remain supported
  without a seat. Their missing office-contact collection still needs the
  interview integration; do not call every notice blank prefilled.
- An unanswered foreign-person choice can be saved/previewed, but must be
  explicitly resolved before sending. No tax-status inference is made. This
  is a source answer, not a form-authorization or owner-approval gate.
- The source-maintenance response now recognizes the implemented TXR-1101
  adapter when signing is configured. TXR-1102 remains source-only. No source
  was uploaded/activated by this local change.

Checking document-list boxes is not attachment proof. Integration must package
the supported documents from interview answers, distinguish pending items,
preserve provider choice, and not stop the listing flow because a completed
seller disclosure has not yet been received. Pending disclosure PR 1341 must
not be accidentally bundled as a finished signing workflow.

## Coordinated schema work - prepared, NOT applied

Supabase CLI 2.81.3 generated
`20261017131634_add_txr1101_listing_drafts.sql`. It preserves all fourteen
existing standalone codes and adds only TXR-1101, not source-only TXR-1102.
It preserves the service-only, SECURITY INVOKER readiness function and adds
the new code and existing private-table RLS checks.

The release check now requires `homeofferflow-release-schema-v2`. This is
intentional: the old production v1 readiness can return true while its CHECK
still rejects TXR-1101. A targeted test proves that old readiness cannot pass
this candidate's release. Apply/read back the migration as part of the
coordinated release, not as an isolated activation. SQL runtime execution and
the v2 live readiness response are still unverified.

Read-only production inspection confirmed:

- the source catalog CHECK already admits TXR-1101/1102;
- the standalone CHECK currently does not admit TXR-1101;
- both private tables have RLS enabled;
- standalone SELECT is scoped to `auth.uid() = agent_user_id`;
- source access retains existing administrative policies; no new grant or
  security-sensitive access was created by this work.

Current Supabase changelog and relevant HTTP/DB compatibility notices were
consulted. This batch does not add legacy TLS, custom operators, encrypted
PGP payloads, ltree or float GiST use. This is not a claim that unrelated
project security findings have been audited or fixed.

The security advisor retained an existing signed-in GraphQL **schema
discoverability** warning for the standalone table. Its actual owner-scoped
SELECT policy was separately verified; do not equate schema discovery with
cross-owner row access or report a clean global audit. No permissions were
changed to silence it. [Advisor explanation](https://supabase.com/docs/guides/database/database-linter?lint=0027_pg_graphql_authenticated_table_exposed).

## Verification

**132 focused checks passed in 10.573 seconds.** Preserved log:
`/private/tmp/hof-txr1101-api-focused-20261017.log`.

This includes actual POST handlers, session verification, PostgREST owner and
version filters, private storage loading and the real delivery coordinator
against httpx MockTransport. No external service receives these fixtures.
The renderer boundary is spied for most API cases; an opt-in test uses the
actual private source and actual renderer through preview and the simulated
delivery adapter, including rejection of changed bytes under the same source
catalog revision. It is **not a real SignWell send or completed-PDF pass**.

Cases cover auth/source failure, browser identity injection, stale sources/maps,
saved-recipient reuse, separate broker/associate plans, wrong-owner reads,
long Unicode payloads, owner-scoped editing, edit races/empty responses,
normalized timestamps, provider field loss and tracked-document reuse after
temporary inspection failure without a duplicate create/send.

The pre-existing platform-intake size-guard assertion initially failed after
the listing-specific size exception was introduced. The original default
guard was preserved as the outer condition, and actual large-listing versus
other-action behavior is exercised. The old check was not removed or weakened.
Whitespace and Python compile checks pass. No full suite was rerun for this
still-unfinished interview integration candidate.

Reproduce (private source path is local-only):

```sh
HOF_TXR1101_SOURCE=/path/to/private/TXR-1101-2026-06-15.pdf \
  /private/tmp/hof-account-context-qa-venv/bin/python -m unittest \
  tests.test_txr1101_api tests.test_txr_1101 \
  tests.test_standalone_form_schema_contract tests.test_production_schema_readiness \
  tests.test_standalone_recipient_preview tests.test_independent_broker_signer \
  tests.test_txr_signing_request_path tests.test_brokerage_form_source_foundation \
  tests.test_standalone_agreement_schema_contract tests.test_platform_form_source_upload -q
```

## Next coherent step

Connect the mobile-first interview, saved-draft edit/review and prepared-document
queue. Use semantic questions, saved listing/seller/professional data and Google
address completion. Do not expose internal answer keys or letter-coded form
selection to agents. Handle refreshRequired without a blind duplicate create.
Then finish the documented visual/provider checks and coordinated release.
No owner decision is needed to continue that implementation.
