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
