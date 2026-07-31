# TXR source-owner handoff

This is a private implementation handoff for the supplied Texas REALTORS®
source PDFs. It does not approve, distribute, or release any form.

## Required source-owner action

An active brokerage administrator must sign in to the brokerage workspace and
upload each source through **Brokerage-approved form sources**. The administrator
must confirm authority for the exact PDF. HomeOfferFlow will keep the source in
private Storage and will not expose it to agents merely because it was uploaded.

The brokerage-level authorization status and each agent's individual TXR/NAR
attestation remain separate controls. A source upload also does not activate a
signing workflow; TXR-1507 still requires mapping, signer-plan, rendered signed
PDF QA, regression, and HomeOfferFlow release-authority approval.

## Supplied source inventory

| Form | Local file | Pages | Expected revision | SHA-256 |
|---|---|---:|---|---|
| TXR-1507 | `TXR1507.pdf` | 2 | `06-15-26` | `ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46f` |
| TXR-1501 | `TXR1501.pdf` | 6 | `06-15-26` | `d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd` |
| TXR-1508 | `TXR1508.pdf` | 1 | `02-25-26` | `b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40` |
| TXR-1506 | `TXR1506.pdf` | 6 | `06-15-26` | `df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4` |

The files remain outside the repository. The fingerprints are for source
identity checking only; they are not a substitute for the source owner's
authorization.

## Current live state

- OnDemand source-vault rows: none.
- No TXR source is approved or available to agents.
- TXR-1507 is the first executable-form candidate once the source-owner gate
  and all release evidence are complete.
