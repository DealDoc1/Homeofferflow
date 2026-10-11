# TREC standalone draft persistence correction

## Scope and production state

- User outcome: save the implemented TREC 62-0, 38-8, and 39-11 documents through the existing agent workflow.
- Production application: `ec70a0f53dd5af621cf961b8f7f7c6241035b274`, Vercel `dpl_45PAVEC53hoqbv5Y5RtqPLX6CbSL` (READY).
- UI release: PR #1303; intentional prebuilt workflow `38106807627` succeeded, including spending, database, canonical-site, PWA, and API checks.
- Database migration: `20261011062619_enable_trec_standalone_drafts.sql`.
- Cost boundary: this persistence correction uses the already-deployed API and requires no additional Vercel build.

## Reproduced failure

The authenticated live TREC-39-11 interview displayed the correct formatted total and retained Google address completion. Preparing the synthetic amendment failed with HTTP 500. The deployment log recorded `create_trec_39_11_draft Could not save the agreement draft.`

The live `hof_standalone_agreements_form_code_check` accepted the eleven TXR codes but none of the three implemented TREC codes. Source intake alone had therefore not made the complete save flow operational.

## Corrected contract

The migration preserves all eleven TXR codes and adds TREC-62-0, TREC-38-8, and TREC-39-11. It also extends the existing service-only schema-readiness function to check the actual persisted-form constraint against all fourteen implemented codes. Existing readiness checks, security-invoker behavior, empty search path, service-only execution privileges, and row ownership policies are preserved.

The official Supabase CLI 2.120.0 generated the migration file. The migration tool initially recorded remote version `20261011063452`; its tracking version was reconciled to the CLI-generated repository identifier `20261011062619`. SQL statements and the migration name were preserved.

Live verification confirmed the expanded CHECK, RLS enabled, and `{ready:true, missing:[], contract:"homeofferflow-release-schema-v1"}`.

## Live application verification

- Synthetic-only draft: `de8c98de-a753-48e7-8edb-52520e909328`.
- One fictional Buyer and one fictional Seller; no real client packet was changed.
- Selected changes: sales price, closing date, and other modifications.
- Cash `125000.25`, financing `374999.75`, total `500000.00` persisted correctly.
- Closing date persisted as `11/20/2026`.
- The modification explicitly states that this is software QA and has no legal effect.
- The UI reported the amendment ready, and its saved row opened a generated private PDF preview.
- The downloaded one-page PDF was visually reviewed: marks 1, 3, and 10 align; all three price amounts, the closing date, address, and QA text are legible without clipping; unselected fields and execution/signature areas remain blank.
- No signature request or additional business email was sent during this verification.

## Remaining evidence and defects

The PDF has no canonical interactive field tree but retains 51 original Widget annotations. The preview is visually correct; remove these orphaned source widgets before treating its static structure as clean. Completed-provider signed-PDF QA is not established by this unsigned review.

A rapid purchase-document handoff reached Guided Forms without opening the amendment automatically. Opening its ready library card succeeded. Reproduce the startup/handoff timing separately before claiming the entire primary path is verified.

The existing browser initially showed an older module after deployment. The canonical served JavaScript matched the release SHA-256 exactly; after a fresh navigation, the current module hid unselected sections and displayed `$500,000.00`. The installed shell is v80.

## Automated validation

- Two new API/migration/readiness form-code contract tests passed.
- Migration preflight: 117 unique ordered migrations, no errors.
- Full regression: 2,475 tests run in 73.463 seconds; passed with one skipped.
- The security advisor's existing GraphQL schema-discoverability notice for this table remains. Its SELECT policy is constrained to the authenticated owner's `agent_user_id`; RLS remains enabled, and no row-access grant changed.
- Repository CI and merge identity are recorded with the merge checkpoint.
