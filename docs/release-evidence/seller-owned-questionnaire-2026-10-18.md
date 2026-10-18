# Seller-owned disclosure questionnaire: local checkpoint

## Batch contract

- Outcome: the seller answers the disclosure, rather than receiving only an agent-prepared review copy. Reuse the same question controls for the agent and seller.
- Scope: offer/listing/account entry points, the existing email-verified seller page, answer-only save/confirmation RPC, existing SignWell sender and concise mobile UI. No native app, billing, real customer packet or third-party communication.
- Verified production baseline: `61e516d0a091646bbff14a00624051d4e328d4fc`, deployment `dpl_2agZyywm1ahG4Pk5tjdaWdZ3YfVx`. This work is not released. Automatic Git deployments remain disabled; no Vercel build or deployment was created.
- Existing candidate integrated disclosure corrections from draft PR #1341 at `c5b6ada2684a89b8216d73249d87f7aa15c982c2` in local merge `91c30246`. This does not claim that PR's outstanding provider QA passed.

## Implemented locally

- The offer workspace has a Seller's disclosure action. Its owner-scoped read carries the saved address and seller contacts, never buyer names or guessed seller answers. Existing unsaved disclosure work is preserved unless the user explicitly starts another.
- The listing handoff remains intact. Individual signed-in sellers can open the disclosure workspace without a brokerage seat. The saved disclosure's property and parties stay fixed when a seller follows an invitation.
- New invitations explicitly enable the questionnaire. Existing review-only links remain read-only. The six-digit email check is retained; revoked/expired credentials cannot load property details. Questionnaire credentials remain in page memory, not device storage.
- The same shared interview includes property items, defects, conditions, repairs, flood information and written explanations, with conditional follow-ups. Saves retain Unicode and explicit Unknown responses. No Yes/No answer is guessed.
- The answer-only service RPC locks the parent draft before the invitation, checks the current version and assigned seller, and cannot change parties, source IDs, ownership or delivery journals. Stale concurrent edits are rejected rather than overwriting newer answers.
- Seller confirmation validates the saved answers, not replacement answers submitted with the confirmation. It records immutable review evidence for that exact content/render version. Further edits invalidate current approval without deleting older review evidence; each listed seller must confirm the current answers.
- The seller can explicitly request separate signing once all seller reviews are current. Recipients come only from saved, assigned questionnaire invitations. No caller-supplied recipient list is accepted and no other signer's bearer link is returned. Existing simultaneous SignWell invitations and signing maps are reused. Buyer acknowledgment requests stay on the authenticated agent path.
- A failed PDF preview never exposes confirmation/signing. The agent can still prepare other documents while the disclosure is incomplete. Automatic inclusion of the completed disclosure in the combined listing/offer packet is **not implemented by this checkpoint**; customer copy does not claim otherwise.

## Verification performed

- 155 focused Python checks pass in 2.159 seconds, including actual-source JavaScript wrappers. Those wrappers include 22 listing/offer handoff cases and the shared interview's conditional/Unicode/save-reopen cases.
- Real isolated PostgreSQL: 52 assertions pass against the actual migrations, including legacy version binding, private grants, stale saves, forged journals, duplicate confirmation, two sellers, retained historical evidence, expiry and revocation. No production database was changed; the local cluster stopped in `finally`.
- The actual seller HTML/scripts ran in one fictional localhost fixture. Email-code entry opened the interview; an edit saved successfully; an unavailable-PDF response kept confirmation hidden. This fixture deliberately does not simulate a completed PDF or provider success.
- Desktop and 390x844 phone layout were reviewed. Document width equals 390px; no horizontal overflow. Screenshots are local fictional UI, not production evidence:
  - `seller-questionnaire-2026-10-18/desktop.png`
  - `seller-questionnaire-2026-10-18/mobile.png`
- No customer/partner email, signature invitation, final signature consent, charge or paid upgrade occurred. No full-suite or completed-provider pass is claimed for this unfinished release candidate.

## Remaining implementation and release work

1. Add the seller-reviewed disclosure adapter to the combined listing/offer packet, with explicit ownership/property/signer matching and truthful pending behavior.
2. Complete the retained v4 disclosure provider check and inspect the actual signed pages; the earlier v3 date-fit failure is not a pass.
3. Differential-check the source currently downloaded from TREC against the previously supplied approved source before changing any source hash. Current public `55-1.pdf` is four pages, printed 05-04-2026, SHA256 `cebab031402fef2d1a16b91e6820b778f3e8971764177700706ec3f6ad8f359b`; the renderer still pins the earlier approved `65a52e...` bytes. No hash check was weakened. The public download is retained in the local QA evidence folder. This is an internal verification task, not a request for owner source authorization.
4. Coordinate both disclosure migrations and the candidate API/UI in one reviewed release, run the frozen full regression once, and verify canonical live behavior. The new migration extends the existing service-only release readiness contract for the questionnaire RPC/columns. Current production remains unchanged.

No new owner action is required for this local workstream. The roadmap goal remains active.
