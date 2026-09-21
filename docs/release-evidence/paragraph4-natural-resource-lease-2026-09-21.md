# Paragraph 4C natural-resource lease interview — September 21, 2026

## Release

- Release name: Paragraph 4C natural-resource lease interview.
- Git commit / pull request: branch `codex/natural-resource-lease-interview`; final commit and pull request are recorded after the verified branch is published.
- Production scope: 20-19 purchase offer interview, validation, contract rendering, review summary, and packet generation.
- Changed packet/form target marker: TREC 20-19 purchase offer, Paragraph 4C Natural Resource Leases.

## Approved source

- Approved source form/template and version: TREC One to Four Family Residential Contract (Resale), TREC No. 20-19, dated 05-04-2026 and effective 07-01-2026.
- Source owner: Texas Real Estate Commission.
- Storage location (private only): repository production asset `20-19_0.pdf`; no new private or brokerage-restricted source was introduced.

## Authorization

- Authority to use this source: public TREC promulgated contract already authorized and active in the HomeOfferFlow purchase-offer workflow.
- Authorized reviewer: Andrew Christian, HomeOfferFlow product owner and counsel.
- Date confirmed: 2026-09-21, under the standing instruction to complete and release the active roadmap without additional approval gates.

## Signing plan

- Each recipient and role: unchanged buyer recipients sign the purchase contract through the existing 20-19 SignWell plan. Paragraph 4C creates no separate addendum or additional signer.
- Signing order: unchanged concurrent signing plan; no sequential order was added.
- Broker oversight / visibility: unchanged from the existing purchase-offer workflow. This release does not require a brokerage seat, broker approval, or a separate source-owner workflow.

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: locally generated 12-page packets in `/private/tmp/homeofferflow-natural-resource-pdf/`; delivered-choice SHA-256 `fc67c6447379a751abcb65d4b61071597ee36ddbb9625ddad4618a2d1ff59d21`; not-delivered-choice SHA-256 `9b5da911ee1110a0c2d0713df414ddc6a2e239c30723d77bbce66e496862866d`.
- Reviewer: Codex visual QA for Andrew Christian.
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: both Paragraph 4C paths were rendered at 240 DPI and visually reviewed. The 4C checkbox, delivered/not-delivered checkbox, and termination-days blank are correctly placed and readable. No initials, signature, date, recipient, or SignWell geometry changed in this release; those existing fields remain covered by the current 20-19 signing plan and regression suite.
- Locked coordinates / known exceptions: Paragraph 4C at `(50,135)`, delivered at `(63,99)`, not delivered at `(63,85)`, and termination days at `(350,60)`. The printed contract fixes Seller delivery at 3 days, so the interview does not ask the user to re-enter or overwrite that printed term. No known placement exception remains.

## Regression

- Dedicated golden scenario added: natural-resource lease not-delivered packet, incomplete-delivery fail-closed checks, contract coordinate assertions, interview collection, validation, review copy, and no-extra-seller-signature assertion.
- Existing buyer-offer regression scenarios run: yes, including all purchase packets, Paragraph 4 addenda, SignWell field maps, saved-draft hydration, agent funnel, and source synchronization tests.
- Test result / evidence: 2,353 tests passed in 74.908 seconds; `git diff --check` passed. Both generated 12-page PDFs were rendered with Poppler and visually inspected.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): Andrew Christian.
- Approval date: 2026-09-21 under the standing roadmap release authorization.
- Approved public-facing scope copy: “Natural resource lease — oil, gas, minerals, water, wind, geothermal, or similar rights.” The interview asks whether Buyer received every lease and, when not delivered, the agreed Buyer termination period after receipt.
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable; this uses the existing public TREC 20-19 source and does not activate a restricted Texas REALTORS® source.

## Deployment decision

- Ready for production: yes, after merge to the verified main commit and inclusion in the next intentional production release.
- Rollback path: redeploy the prior Ready production commit; no migration or customer-data rollback is required.
- Post-deploy verification owner: HomeOfferFlow / Codex. Verify the canonical guided interview, both Paragraph 4C choices, a read-only production release check, and Vercel runtime health without creating a customer packet.
