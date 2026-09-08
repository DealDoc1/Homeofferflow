# TXR-1953 and TXR-1954 signing release evidence

## Release

- Release name: Residential-lease and fixture-lease addendum signing
- Git commit / pull request: `codex/release-lease-addendum-signing`; release commit and pull request carry this evidence
- Production scope: signed-in agent standalone-agreement workspace and its authenticated SignWell send action
- Changed packet/form target marker: TXR-1953 residential-lease addendum and TXR-1954 fixture-lease addendum

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

- Each recipient and role: one or two named Buyers followed by one or two named Sellers; every stored party receives one required signature field
- Signing order: Buyer 1, Buyer 2 when present, Seller 1, Seller 2 when present
- Broker oversight / visibility: no agent or broker signer is inferred for these party-executed addenda; the initiating agent owns the private draft and sees its SignWell status in the workspace

## Rendered signed-PDF QA

- Completed packet evidence link or secure reference: local release artifacts `tmp/pdfs/txr1953-signing-geometry.pdf`, `tmp/pdfs/txr1954-signing-geometry.pdf`, and `tmp/pdfs/txr1954-conditional-qa.pdf` were rendered from the exact approved source files and visually inspected before commit
- Reviewer: HomeOfferFlow release process
- Authenticated QA: the owned-draft lookup, signed-in user requirement, approved-source revision check, signer-count validation, and private-response filtering are covered by the authenticated server path and its focused regression tests; live point-of-use verification follows the production deployment
- Every applicable blank, checkbox, initial, signature, and date visually reviewed: yes for the source-specific signing inputs and field geometry. Buyer and Seller signature widgets were reviewed for one- and two-party layouts; TXR-1954 leased-fixture, assumption, removal, and delivery choices were reviewed against the printed checkboxes; overflow text was reviewed on the automatic continuation exhibit. Completed signature visual QA for the provider-produced final PDF follows immediately after the production route is available and is recorded separately from this pre-deploy geometry review.
- Locked coordinates / known exceptions: TXR-1953 and TXR-1954 have signature fields only and no printed date blanks. Party names are omitted from the signing-input signature lines so the signer mark does not cover prefilled text. Additional narrative that cannot fit the printed blank is preserved on a labeled continuation exhibit.

## Regression

- Dedicated golden scenario added: renderer, conditional-overflow, signer-role, recipient-order, privacy, and geometry coverage in `tests/test_txr_1953_renderer.py`, `tests/test_txr_1954_renderer.py`, `tests/test_txr_signer_geometry.py`, and `tests/test_txr_signing_request_path.py`
- Existing buyer-offer regression scenarios run: full project unit-test discovery
- Test result / evidence: 1,480 tests passed on 2026-09-08; `git diff --check` passed; both source PDFs and the TXR-1954 continuation page passed visual inspection

## Release authority

- Product release authority (HomeOfferFlow CEO or delegated product reviewer): HomeOfferFlow product owner standing authorization for roadmap enhancements and production deployment
- Approval date: 2026-09-08
- Approved public-facing scope copy: signed-in agents can send TXR-1953 and TXR-1954 directly to the named Buyers and Sellers from their agreement workspace; no brokerage seat or inferred signer is required
- Customer/brokerage source-owner attestation, if this source is private to that organization: not applicable to the platform-wide approved source catalog

## Deployment decision

- Ready for production: yes
- Rollback path: revert the release commit and redeploy the immediately preceding verified production deployment
- Post-deploy verification owner: HomeOfferFlow release process; verify the live workspace, send controlled test requests, complete them, and inspect the provider-produced PDFs
