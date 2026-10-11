# TREC 39-11 live source activation

## Intended outcome and production boundary

- Outcome: agents can open the deployed Amendment to Contract interview using the exact official source.
- Scope: production form-source constraint, authenticated admin source intake, and the TREC-39-11 library card.
- Production revision: `8725f4832ad53cefc35fb3243417389365207583`, Vercel `dpl_2TGa1NcoQFS2TG6pmJ7hAKEpVCV8` (READY).
- Cost constraint: use the already-deployed workflow; no Vercel deployment was needed for this source activation.
- Required evidence: live constraint, approved source row, private PDF presence, source hash, and authenticated card/interview access.

## Reproduced failure and correction

Authenticated owner intake failed with HTTP 500. The deployment log recorded `upload_platform_form_source Could not record the private source approval.` The live `hof_brokerage_form_sources_form_code_check` omitted TREC-39-11 even though the production application and repository migration supported it.

Applied the SQL already committed at `supabase/migrations/20261005110000_expand_trec_39_11_source_code.sql` using the Supabase migration tool. The tool initially recorded remote version `20261010205457`, named `expand_trec_39_11_source_code`. After confirming that the repository version was absent and only this exact named migration had the generated version, its tracking identifier was reconciled to `20261005110000`. The original SQL and migration statements were preserved; no schema or application records changed during that bookkeeping repair.

The live constraint now contains TREC-39-11 and all existing supported codes. RLS remains enabled. The security advisor reported no finding for the source table.

## Exact source and live verification

- Official URL: https://www.trec.texas.gov/sites/default/files/pdf-forms/39-11.pdf
- Printed revision visually reviewed: `05-04-2026`.
- Pages: 1; byte size: 530831.
- SHA-256: `d12909bcbd014080948eb6f9771231ba1b1d98c64eaf07e87ab0faa1118b8d36`.
- Downloaded official file exactly matches the repository's exact-source fixture.
- Saved through the authenticated platform-admin UI with OnDemand source provenance.
- UI confirmed `TREC-39-11 05-04-2026 saved privately and ready for the draft/signing queue.`
- Database row is approved; matching object exists in private storage.
- After refreshing the application, the Amendment to Contract card displays `Start contract amendment` and opens the live interview.
- No real client packet was changed and no email was sent by this form activation.

## Interview improvement candidate

- Unselected detail panels use explicit hidden display, preventing the shared label grid style from exposing unnecessary questions.
- The displayed total accepts the same comma-formatted amounts as the interview inputs. `125,000` plus `375,000`, and `125,000.25` plus `374,999.75`, both display `$500,000.00`.
- Change choices have labeled tap areas measuring at least 44px high; desktop uses two columns and the 390px mobile viewport uses one.
- All nine detail panels were exercised through selected and cleared states in the production-styled browser fixture. Only the selected questions were visible.
- Option extension and option waiver remain mutually exclusive in the browser.
- Mobile form width was 356px for both client and scroll width: no horizontal overflow.
- The existing production address-input observer includes `propertyAddress`; the Google completion path was not changed.
- The fixture loads the actual production styles without loading account scripts, avoiding an inaccurate unstyled QA view.
- JavaScript syntax check and three monetary display runtime cases passed.
- Focused TREC-39-11 suite: 12 tests passed.
- Full regression: 2,473 tests run in 77.377 seconds; passed, with one skipped.
- Supabase migration preflight: 116 unique ordered migrations, no errors.
- Vercel Usage page for Sep 22–Oct 22 showed `$0.02 / $20.00` included credit used. Provider notes usage may be up to one hour old. The release uses the existing prebuilt workflow and its additional live spend check.

This candidate changes the interview presentation and displayed total only. It does not change server parsing, PDF rendering, signature coordinates, recipient roles, or parallel invitations. Completed-provider PDF QA remains a separate form-coverage task rather than a claim made by this UI release.

## Outstanding verification

The current production interview still has the previously observed conditional-label visibility issue until the tested presentation candidate is deployed. Post-deploy canonical browser verification and a fresh synthetic saved amendment/PDF review are required.

Completed-provider signature PDF QA remains outstanding. Source activation, unsigned rendering, and completed signing must remain separate evidence claims.

## Related agent route check

On the canonical site, the authenticated `/?agent=1&workflow=purchase` handoff opens the selected Purchase path and the next package question. The signed-in owner account is connected to OnDemand with active membership. This does not establish brokerage-admin branding or invitation QA for Tyler's account.
