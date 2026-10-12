# Purchase provider completion and status reporting

## Scope and current baseline

- Existing fictional, nonbinding QA document only: `6ad57745-57bc-4bd0-8324-e7d68b51c86e`; no new document or repeated invitation.
- Customer production baseline `a9f636f226f53aed0001a126c8252067257a1f96`, READY `dpl_2LPhspe1wD7Axovg9rFhLzgjcrms`.
- Outcome: finish the actual provider review where authorized, and correct the protected operator status reader so casing/terminal states cannot falsely leave a test awaiting completion.
- No source PDF, signing map, real client record, customer signing settings, access role, credential, schema or charge is changed.

## Actual provider and signing-session evidence

- SignWell's existing session had expired. Its existing Google login restored the same account without new credentials/permissions. Documents count remains 143; the exact release-tagged QA packet is Sent, addressed to QA Signer A and QA Signer B.
- Opened only the matching QA builder; no real client packet was opened, edited or resent.
- Opened the existing Andrew Gmail QA invitation and its native review control. No signer URL was copied into an artifact or response.
- The actual signing screen explicitly says `This is Not Legally Binding` and confirms it was created in test mode. Vendor documentation agrees: https://developers.signwell.com/reference/createdocument.
- In that same test-only session, applied the fictional labels `QSA` and `QA Signer A` to its initial/signature fields. The UI advanced from 4/15 auto-filled dates, to 11/15 with initials, then the final step with all first-recipient fields prepared. These are not Andrew's personal signature or client signatures.
- The final `Agree & Finish` separately accepts SignWell's Electronic Signature Disclosure, which covers the broader relationship/future communications, not just the document. Read https://www.signwell.com/electronic-signature-disclosure/ and requested that specific at-action decision. Final acceptance remains untouched unless the human explicitly approves or completes it.
- No completed-provider PDF or signing-QA pass is claimed from prepared fields. The other recipient and final provider PDF review still remain to be completed.
- Normal vendor completion receipts may occur when the existing test is completed; no new invitation, document, reminder or business email is created by this work.

## Reproduced status defect and correction

- Existing code compared raw provider status only with lowercase `completed`. `Completed`, whitespace variants, terminal cancellation/decline/expiry, and arbitrary provider strings were not safely classified.
- A failing regression reproduced all seven cases before the fix.
- Normalize approved enum values, handle completion and terminal states accurately, and return `unknown` for unrecognized text rather than reflecting arbitrary provider strings/possible URLs.
- This correction applies only to protected QA receipt/status reporting. It does not change customer signing, send/retry behavior, consent, provider fields or roadmap pass flags.
- Every status test verifies that checking remains read-only: no provider POST, database PATCH, resend or credential exposure.
- 38 focused tests passed after the correction. Full regression and exact release evidence are recorded at their completed checkpoints below.
- Full local candidate: 2,522 tests in 84.752 seconds, OK (one skipped). Patch whitespace passes.
- Only the specific first-recipient QA consent tab is retained as a handoff. Its private signing URL is not persisted in repository evidence. The email/navigation tab was closed.

## Actual released checkpoint

- PR #1316 passed exact-head CI `38269673575` (regression, golden rendering, standalone geometry, schema preflight, whitespace) and merged as `b13dac13e410b9a615b4ec174a131790e9f1bc8a`.
- Intentional release `38270426931` succeeded: cloud regression 2,522 tests, OK (two environment-dependent skips), coordinated schema check, spend guard, prebuilt build/deploy, canonical PWA/API/packet checks passed.
- READY production `dpl_CCLtZoVEoqo5rdR6iRYC4P23CM67`, both canonical domains aliased, exact SHA confirmed. Pre-build snapshot 15:30:48 UTC: $0.03/$20 used, $19.97 unconsumed, $3 reserve. Not a future billing guarantee.
- Authenticated canonical owner Admin > Check test status successfully checked the recorded QA identity and returned awaiting completion. No Send action, provider POST, DB mutation or resend occurred. Actual Completed-state handling is regression-verified, not claimed against a completed live test.
- Error-level deployment log sample 15:31:10–15:39:24 UTC: no matching logs. No universal outage-free or final signed-PDF claim.
- First recipient's broader disclosure remains unaccepted pending the specific human decision. Second-recipient completion and executed-PDF review remain outstanding; no signing-QA pass or provider completion was fabricated.

## Next observed UX defect

- During canonical verification, opening the owner account and immediately selecting Admin initially showed Loading admin dashboard. When the startup/profile work settled, the visible panel was Dashboard while keyboard focus remained on Admin. Selecting Admin after initialization stayed active and allowed the read-only status check.
- Record this startup/tab-selection race for the next bounded UX workstream. Do not count it as fixed by this API-only release, an access problem, or a reason to resend the QA packet.

## Approved first-recipient finalization

- The human explicitly answered `Yes—finalize this QA packet` to the scoped final electronic-disclosure question. Accepted `Agree & Finish` only on the existing test session, using the fictional QA Signer A signature already prepared.
- Actual provider result: `Thanks for filling out your document.` The completion screen states that the final copy will be emailed once everyone completes it. This is recipient completion, not whole-document completion.
- The owner document list now shows the exact same document `In Progress`; its recipient tooltip explicitly says `QA Signer B has not completed the document.` Manage Recipients shows the original two approved inboxes unchanged. Did not select, edit, replace, remind, resend or mark a document signed.
- First-recipient completion screenshot: `/private/tmp/hof-provider-completion.bBz0N0/qa-signer-a-completed.jpg`. Owner status screenshot: `/private/tmp/hof-provider-completion.bBz0N0/qa-packet-first-signer-in-progress.jpg`.
- The connected Gmail search found only the original Andrew invitation. The in-app Gmail account switcher offered only Andrew's current account; the open Chrome Gmail tab is also Andrew's inbox. No existing second-inbox session was available in these checked surfaces. Requested opening or completing the already sent invitation in `brewbqinfo@gmail.com`, not another approval or a duplicate send.
- The first-recipient PDF link did not yield a registered new browser tab or an exact matching purchase-QA download in the bounded filesystem check. No completed provider PDF was acquired; do not substitute an unsigned local rendering or claim final visual QA.
- Second-recipient completion and actual completed-PDF review remain outstanding. No new Vercel deployment is needed for this evidence-only checkpoint; production behavior remains unchanged.
