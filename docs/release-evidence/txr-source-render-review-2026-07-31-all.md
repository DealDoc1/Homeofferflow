# TXR source render review - 2026-07-31

## Scope

This review used the four privately supplied Texas REALTORS(R) source PDFs
authorized by the product owner. Each source was rendered with the current
source-specific renderer and inspected as a rendered PDF. The source PDFs are
not checked into the repository.

This is a source/render QA record only. It does not activate, send, or sign any
restricted form.

## Source inventory reviewed

| Form | Pages | Revision printed on source | SHA-256 |
|---|---:|---|---|
| TXR-1501 | 6 | 06-15-26 | `d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd` |
| TXR-1506 | 6 | 06-15-26 | `df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4` |
| TXR-1507 | 2 | 06-15-26 | `ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46` |
| TXR-1508 | 1 | 02-25-26 | `b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40` |

All four source files were static PDFs with no AcroForm fields. The current
renderers preserve the source pages and overlay only the explicitly supplied
intake values.

## Rendered visual review

### TXR-1501 - Residential Buyer/Tenant Representation Agreement, Long Form

- All six source pages were preserved.
- Party names, client contact values, brokerage/associate identity, market area,
  term dates, compensation values, intermediary choice, and printed-name blocks
  were visible in the intended sections.
- The renderer left Special Provisions and source boilerplate untouched.
- The signer map remains deliberately separate from the purchase packet and
  requires an explicit brokerage signer plan: clients plus the authorized
  associate or clients plus the authorized broker.

### TXR-1506 - General Information and Notice to Consumers

- All six source pages were preserved.
- The optional notice text, provider name, and consumer names were visible on
  the final source page; source notice text and footer initials areas remained
  intact.
- The signer map supports one or two consumer recipients and requires an
  explicit authorized associate or broker acknowledgement plan because the
  source includes a brokerage execution line.

### TXR-1507 - Residential Buyer/Tenant Representation Agreement, Short Form

- Both source pages were preserved.
- Client names, brokerage identity, market area, term dates, service level,
  compensation, intermediary choice, and broker/associate/client printed names
  were visible and readable in the intended sections.
- The existing two-page render was visually inspected at source scale. The
  current implementation still stops at unsigned overlay QA; it does not claim
  that SignWell field placement or completed-signature appearance is approved.

### TXR-1508 - Unrepresented Customer Showing Form

- The one source page was preserved.
- Property address, brokerage and associate identity, customer names, and the
  two other-broker-agreement choices were visible in the expected areas.
- The scope-limiting unrepresented-customer acknowledgement remains required in
  the application flow. The signer map requires an explicit broker-or-associate
  acknowledgement plan plus customer recipients.

## Remaining gates before any restricted-form send/sign release

The following are still required for each form independently:

1. Source owner or authorized brokerage administrator uploads the exact source
   bytes to the private source vault and attests to the revision.
2. The source owner confirms the signer roles and whether the broker, associate,
   clients/consumers, or a combination must sign or initial.
3. SignWell fields are placed on the exact source revision and visually checked
   against every signature, date, and initials line.
4. A completed signed PDF is downloaded and visually inspected page by page.
5. Release authority approves that form's workflow for production.

Until all five gates pass, the form must remain a private draft foundation and
must not be advertised as an active HomeOfferFlow send/sign capability.
