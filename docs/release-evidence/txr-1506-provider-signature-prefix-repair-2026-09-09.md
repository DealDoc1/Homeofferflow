# TXR-1506 provider-signature prefix repair — 2026-09-09

## Release

- Release name: TXR-1506 provider signature-rule alignment repair
- Git commit / pull request: release commit carrying this evidence
- Production scope: the signed-in agent TXR-1506 review-and-send workflow
- Changed packet/form target marker: TXR-1506 General Information and Notice to Consumers

## Approved source

- Approved source form/template and version: TXR-1506, revision 06-15-26
- Source vault: the approved private TXR-1506 source in the HomeOfferFlow source vault; it is revalidated by the authenticated server before a preview or signature request
- Source review: page 6 of the exact supplied source PDF was rendered at SignWell's 96-DPI, top-origin US Letter coordinate system and visually reviewed

## Authorization

- Authority to use this source: the platform-wide approved HomeOfferFlow source catalog and standing HomeOfferFlow product authorization for signed-in agents
- Agent attestation: signed-in agents use the shared catalog without a brokerage-seat requirement and remain responsible for transaction-specific review before sending

## Signing plan

- Each recipient and role: one or two named consumers plus one deliberately selected broker or broker-associate acknowledgement signer
- Signing order: the selected broker or broker-associate and each named consumer receive only their corresponding acknowledgement fields
- Repair: the provider signature field now begins after the source's printed `By:` prefix at x=80, retains the source-rule right edge at x=250, and ends at y=825 above the printed signature caption

## Rendered signed-PDF QA

- Source-specific geometry review: the page-six provider signature/date row and both consumer rows were overlaid on the approved source and visually inspected; the provider field no longer covers the `By:` prefix, while the date remains in the printed Date column
- Completed signature visual QA: the controlled single-signer completed-PDF visual review recorded in `docs/release-evidence/txr-1506-single-signer-signed-pdf-qa-2026-09-07.md` remains applicable to the workflow. This repair narrows the provider widget horizontally without changing recipients, signing order, source content, or the completed-PDF result boundary.
- Authenticated QA: the authenticated owned-draft, approved-source revision, signer-plan, recipient-confirmation, and private-response paths are covered by the existing TXR signing request regression suite

## Regression

- Dedicated geometry coverage: `tests/test_txr_1506_renderer.py` and `tests/test_txr_signer_geometry.py` assert the provider field begins after the printed prefix, ends at the same source-rule edge, and clears the printed caption
- Signing request coverage: `tests/test_txr_signing_request_path.py`
- Test result: 24 focused signing tests passed and full project discovery passed with 1,530 tests on 2026-09-09

## Release authority

- Product release authority: HomeOfferFlow product owner standing authorization for roadmap enhancements and production deployment
- Approval date: 2026-09-09
- Approved public-facing scope copy: unchanged; agents review the completed TXR-1506 document and explicitly confirm recipients before SignWell receives a request

## Deployment decision

- Ready for production: yes
- Rollback path: revert the release commit and redeploy the immediately preceding verified production deployment
- Post-deploy verification: confirm the canonical site responds and use this map for all newly created TXR-1506 signature requests; previously sent packets retain their original fields
