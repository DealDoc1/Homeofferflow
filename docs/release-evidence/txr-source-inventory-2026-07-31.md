# TXR source inventory — 2026-07-31

## Purpose

This inventory records the exact private source PDFs found in Andrew
Christian's authorized HomeOfferFlow source folder. It is an inspection
record, not an activation record. The files remain private and are not copied
into the public repository or exposed to agents through the browser.

## Candidate sources inspected

| Form | Local source | Revision shown in PDF | Pages | AcroForm fields | SHA-256 | Visual inspection |
|---|---|---:|---:|---:|---|---|
| TXR-1501 | `TXR1501.pdf` | 06-15-26 | 6 | 0 | `d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd` | All 6 rendered pages inspected |
| TXR-1506 | `TXR1506.pdf` | 06-15-26 | 6 | 0 | `df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4` | All 6 rendered pages inspected |
| TXR-1507 | `TXR1507.pdf` | 06-15-26 | 2 | 0 | `ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46` | Both rendered pages inspected |
| TXR-1508 | `TXR1508.pdf` | 02-25-26 | 1 | 0 | `b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40` | The rendered page inspected |

## Findings

- These are static PDFs with no AcroForm fields; each implementation will
  require a document-specific coordinate map or an approved source-specific
  renderer.
- TXR-1501 and TXR-1507 contain broker/associate and client signer areas.
- TXR-1506 contains acknowledgment areas for the consumer and broker/agent.
- TXR-1508 contains broker/associate acknowledgment plus customer initials and
  acknowledgment lines; it is a distinct unrepresented-showing workflow.
- Source revision, signer plan, rendering, and completed-signature QA must be
  recorded separately for each form. One form's QA cannot be reused for
  another.

## Activation status

All four forms remain **source-gated and inactive**. Before any form can be
created, sent, or signed in production, an authorized source owner must:

1. Upload the exact PDF privately to the intended brokerage source record.
2. Attest to the fingerprint and revision.
3. Approve the form-specific field map and signer plan.
4. Complete rendered-PDF QA and completed-signature visual QA.
5. Receive HomeOfferFlow release-authority approval.

The Texas REALTORS®/NAR membership gate is necessary but does not replace
these source and QA gates.
