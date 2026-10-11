# Purchase contract contact and execution alignment correction

## Outcome and release boundary

- Outcome: newly generated TREC 20-19 purchase packets seat contact details and full signing rectangles within the correct source blanks.
- Scope: `lib/trec_20_19_contacts.py` (trec 20 19 contacts), the synchronized verified/staging renderer, production adapter, regression tests, and golden packet manifest.
- Verified prior production: `ec70a0f53dd5af621cf961b8f7f7c6241035b274`, READY deployment `dpl_45PAVEC53hoqbv5Y5RtqPLX6CbSL`.
- Cost boundary: automatic Git deployments remain disabled. Use one intentional prebuilt production release after protected checks and the existing live spend check. Vercel Usage showed $0.03 of $20 included infrastructure credit used for Sep 22-Oct 22; usage may be up to one hour old.

## Approved source and authorization

- Approved source: existing public TREC 20-19, printed source revision 05-04-2026, `20-19_0.pdf`, SHA-256 `be3fa154f00476a674c73ba20f6c589111a905bc1e0894e0d5786b714f16f8d4`.
- No source PDF, printed terms, or transaction choices were changed. No new source vault entry or restricted TXR source is involved.
- Authorization and release authority: the owner directed correction and deployment of the discussed workflow defects without repeated approval.
- Agent attestation: no new form-access attestation, brokerage seat, or approval gate was added.

## Reproduced defects and corrected behavior

- Read-only review of the owner's completed purchase packet showed contact values below their named page-11 rules, an agent firm name substituted for the page-8 agent address, and footer initials below their blanks. The audit trail establishes creation on September 18 and completion on October 8; signing the older packet could not apply a later renderer update.
- Current code still used the incorrect contact baselines. Earlier row tests allowed values below the intended rules. The new regression measures full text bounds against the actual source edges instead.
- Broker firm, broker license, associate name, team, email, phone, and associate license now occupy their own measured source rows. A supplied agent mailing address uses the correct address blanks. A missing address remains blank; a firm name is never invented as an address.
- Long or Unicode contacts fit within bounded blanks or remain complete in an initialed contact continuation. When the exact Buyer address/email already appears in an attached temporary-lease continuation, the contract refers to it rather than adding a duplicate continuation.
- The entire first signature rectangle previously ended at PDF top-origin y=339.75, beyond the printed execution rule at 336.27. Both signature/date rectangles now end above their own Buyer/Seller rules. Main footer initials also end above the underscore blanks.
- The production render snapshot records `trec-20-19-2026-10-11-contacts-execution-v1` for the main contract.

## Signing plan

Recipient roles, required fields, locked signature dates, page offsets, and simultaneous invitations are preserved. Existing Seller recipients can initial an added contact continuation, but the correction never introduces an otherwise absent Seller invitation. Historical provider documents and the owner's signed contract were not modified, canceled, replaced, or resent. No client email was sent.

## Rendered signed-PDF QA and authenticated QA

- The actual completed client PDF was reviewed read-only on pages 2, 3, 5, 6, 7, 8, 10, and 11, plus its audit text. It provides failure evidence, not evidence of the corrected map.
- Three clearly labeled synthetic changed-page specimens were rendered: one Buyer, two Buyers, and very long Unicode contact text. All ten changed pages were visually inspected, including source pages 8, 10, 11 and the long-contact continuation. No clipping, wrong-row contact values, or rectangles crossing their source execution rules remained.
- These specimens show synthetic field boxes, not provider-completed signature artwork. Completed signature visual QA for the **new** map is not yet verified.
- Authenticated QA access was restored in SignWell using the existing Google session. No test or customer request was submitted during this local correction.
- Source-bound tests cover both Buyer rows, all main footer initials, contact semantics, address aliases, and exact long-answer retention with continuation page/recipient checks. Existing four-party lease geometry checks cover the corresponding Seller execution rows.

## Regression and checkpoint

- Initial full regression exposed two duplicate-continuation failures; these were corrected by referencing the exact already-attached temporary-lease notice. Do not cite that first run as green.
- Final affected suite: 38 tests passed, including the temporary-lease long-address branches.
- The corrected source maps remain synchronized. Golden signing geometry was deliberately refreshed only after the source-bound assertions and synthetic visual inspection.
- Final full regression: 2,481 tests in 74.962 seconds; passed with one skipped.
- All twelve golden purchase-packet scenarios match the deliberately reviewed baseline; standalone TXR signing geometry is unchanged and passes its separate baseline check. All 117 migrations pass branch preflight; whitespace and renderer synchronization checks pass.
- Protected CI, exact release revision, and canonical production verification will be recorded at their actual checkpoints.

## Protected-main release checkpoint

- PR #1305 passed independent run `38150345669` and merged as `77837a23b52f2730b314b8a2602b38afc668b722`.
- Intentional release `38150681123` passed the exact-commit full regression, then stopped on a trailing blank line in the previously merged standalone-draft migration. The Vercel deployment job was skipped: no Vercel build or deployment occurred.
- Removed that single blank line without changing SQL statements or reapplying the already-successful live migration. The full comparison against the prior production revision is checked, not narrowed to bypass the formatting failure.

## Deployed and canonical verification

- PR #1306 passed independent run `38151019739` and merged as `da511a0d242d3026e7b716ad6cfbfeea3c4c49a5`.
- Corrected intentional release `38151273004` succeeded. Its exact-commit regression, release preflight, live schema readiness, spend check, prebuilt build/deploy, canonical site, PWA shell, and packet-runtime checks all passed.
- One actual Vercel deployment: `dpl_96vs29Ewd4sSrezwrTQ7nRuYEHnS`, READY, production, exact SHA `da511a0d242d3026e7b716ad6cfbfeea3c4c49a5`. Both `www.homeofferflow.com` and `homeofferflow.com` alias this deployment.
- Live spend check: $0.03 infrastructure credit consumed, $19.97 unconsumed, $3.00 reserved. The failed earlier GitHub verification attempt created no Vercel deployment.
- Separate canonical API check returned `ok: true`, no errors, TREC 20-19 production, SignWell enabled in production mode. Home, OnDemand, Terms, Privacy, Disclaimer, and e-sign consent returned HTTP 200.
- No error-level runtime logs matched this deployment during 15:29:00-15:31:36 UTC. This short sample is not proof that every transaction path was exercised.
- The final Unicode continuation was rerendered and visually rechecked after the address-heading correction; all entered text remains legible and retained.
- No real client packet was generated, modified, resent, or signed. Completed-provider PDF inspection for this new map remains pending; deployment and local visual evidence do not substitute for it.

This is a corrective release, not a claim that every supported form or provider signing matrix is complete. Fresh completed-provider inspection remains explicit follow-up work.
