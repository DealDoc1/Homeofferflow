# Restricted-form source preflight - 2026-08-08

The authenticated QA helper now performs a read-only live brokerage-source
preflight before creating any restricted TXR draft. It requires the API to
report `readyForRestrictedDraft: true`, which represents brokerage
authorization, source approval, and source attestation together.

If any source is missing or not ready, the helper fails before draft creation.
Seller disclosure review-only previews remain separate and do not use the TXR
preflight because they have their own TREC-55-1/TREC-61-0 source gate.

This is a QA safety improvement, not a signing release. Completed rendered
PDF and completed-signature visual QA are still required before production
enablement.

Verification:

- 532 local tests passed.
- Authenticated TXR source-preflight tests passed.
- GitHub Actions run `31251854198` passed.
