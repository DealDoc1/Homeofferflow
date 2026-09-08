# TXR-1953 and TXR-1954 signing release evidence

## Release

- Release name: Residential-lease and fixture-lease addendum signing and automatic purchase-offer assembly
- Git commit / pull request: `codex/paragraph4-auto-package-20260908`; release commit and pull request carry this evidence
- Production scope: signed-in agent standalone-agreement workspace plus the 20-19 purchase offer interview, contract packet, and authenticated SignWell send action
- Changed packet/form target marker: 20-19 purchase offer contract packet, TXR-1953 residential-lease addendum, and TXR-1954 fixture-lease addendum

## Approved source

- Approved source form/template and version: TXR-1953 / TREC 51-1 and TXR-1954 / TREC 52-1, both revision 11-07-2022
- Source owner: platform-wide approved source catalog; no brokerage-specific source owner is required for this shared workflow
- Storage location (private only): Supabase `brokerage-form-sources` source vault; the existing approved source revision is revalidated by the authenticated server before every preview and signing request

## Authorization

- Authority to use this source: approved shared HomeOfferFlow source catalog and standing HomeOfferFlow product authorization to make the forms available to all signed-in agents
- Authorized reviewer: HomeOfferFlow product owner and release process
- Date confirmed: 2026-09-08
- Agent attestation: signed-in agents use the shared source catalog without a brokerage-seat requirement and remain responsible for transaction-specific review before sending

## Signing plan

- Each recipient and role: one or two named Buyers followed by one or two named Sellers; every stored party receives one required signature field. Purchase-offer packets reserve recipient IDs 1 and 2 for Buyers and 3 and 4 for Sellers so Paragraph 4 forms share the same Seller roles as any Seller temporary lease.
- Signing order: Buyer 1, Buyer 2 when present, Seller 1, Seller 2 when present
- Broker oversight / visibility: no agent or broker signer is inferred for these party-executed addenda; the initiating agent owns the private draft and sees its SignWell status in the workspace

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: local release artifacts `tmp/pdfs/txr1953-signing-geometry.pdf`, `tmp/pdfs/txr1954-signing-geometry.pdf`, and `tmp/pdfs/txr1954-conditional-qa.pdf` were rendered from the exact approved source files and visually inspected before the standalone release. For this purchase-offer integration, `/private/tmp/hof-p4-qa/combined-paragraph4-offer.pdf` was rendered from the exact TXR-1953 and TXR-1954 source files into a 14-page combined packet; contract pages 1 and 9 and addendum pages 13 and 14 were visually inspected.
- Reviewer: HomeOfferFlow release process
- Authenticated QA: the owned-draft lookup, signed-in user requirement, approved-source revision check, signer-count validation, and private-response filtering are covered by the authenticated server path and its focused regression tests; live point-of-use verification follows the production deployment
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: yes for the source-specific signing inputs and field geometry. Buyer and Seller signature widgets were reviewed for one- and two-party layouts; TXR-1954 leased-fixture, assumption, removal, and delivery choices were reviewed against the printed checkboxes; overflow text was reviewed on the automatic continuation exhibit. The combined purchase-offer render correctly checked both Paragraph 4 choices on page 1 and both Paragraph 22 addendum choices on page 9. Completed signature visual QA for the provider-produced final combined PDF remains a post-deploy check after the controlled test recipients finish signing; it is not represented here as completed.
- Locked coordinates / known exceptions: TXR-1953 and TXR-1954 have signature fields only and no printed date blanks. Party names are omitted from the signing-input signature lines so the signer mark does not cover prefilled text. Additional narrative that cannot fit the printed blank is preserved on a labeled continuation exhibit. In the combined packet, TXR-1953 Buyer/Seller fields map to page 13 with recipient IDs 1/3, and TXR-1954 Buyer/Seller fields map to page 14 with recipient IDs 1/3.

## Regression

- Dedicated golden scenario added: renderer, conditional-overflow, signer-role, recipient-order, privacy, and geometry coverage in `tests/test_txr_1953_renderer.py`, `tests/test_txr_1954_renderer.py`, `tests/test_txr_signer_geometry.py`, and `tests/test_txr_signing_request_path.py`; automatic Paragraph 4 packet assembly, contract checkboxes, private source hydration, interview behavior, and Buyer-then-Seller routing are covered in `tests/test_controlled_launch.py`, `tests/test_paragraph4_source_hydration.py`, `tests/test_paragraph4_offer_interview.py`, and `tests/test_seller_temporary_lease_production_signwell.py`.
- Existing buyer-offer regression scenarios run: full project unit-test discovery
- Test result / evidence: 1,492 tests passed on 2026-09-08; 76 focused tests passed; verified production/staging source copies have identical SHA-256 hashes; JavaScript syntax and `git diff --check` passed; both source PDFs, the TXR-1954 continuation page, and the 14-page combined purchase-offer packet passed pre-deploy visual inspection. Production previously accepted controlled standalone TXR-1953 and TXR-1954 drafts after the database allowlist repair, exposed the expected Buyer and Seller roles, and accepted both SignWell sends to the supplied QA recipients.

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): HomeOfferFlow product owner standing authorization for roadmap enhancements and production deployment
- Approval date: 2026-09-08
- Approved public-facing scope copy: signed-in agents answer plain-language lease questions inside the purchase-offer interview, and HomeOfferFlow automatically includes TXR-1953 and/or TXR-1954 in the offer package for the named Buyers and Sellers; no brokerage seat or separate form-library detour is required
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable to the platform-wide approved source catalog

## Deployment decision

- Ready for production: yes
- Rollback path: revert the release commit and redeploy the immediately preceding verified production deployment
- Post-deploy verification owner: HomeOfferFlow release process; verify the canonical interview, production packet assembly, and controlled combined signature send. Inspect the provider-produced completed combined PDF when the test recipients finish signing.
