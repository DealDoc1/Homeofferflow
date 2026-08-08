# Verified production release — 3abba8d — 2026-08-08

## Scope

This release bundles the already-reviewed HomeOfferFlow platform and seller-QA
hardening changes. It does not change the protected TREC 20-19 packet mappings,
legal-form source PDFs, signer coordinates, or SignWell send behavior.

## Evidence

- Repository: `DealDoc1/Homeofferflow`
- Main commit: `3abba8dcd6a60738a968d51e8aa29176eb088c3c`
- GitHub test workflow: `31231676077` — successful
- Intentional production workflow: `31231676078` — successful
- Vercel deployment: `dpl_D2ExS1P7mfwuBMNvF4LoxbTktABC` — `READY`, production
- Deployment commit: `3abba8dcd6a60738a968d51e8aa29176eb088c3c`
- Canonical `https://www.homeofferflow.com/`: HTTP 200
- Runtime error check after release: no errors in the selected two-hour window
- Local full suite: 480 tests passed

## Release boundaries

- Git deployments remain disabled under the Vercel Hobby-cap policy.
- The release used the confirmation-gated production workflow and one
  intentional production deployment.
- Buyer-representation, seller-disclosure, listing, and other restricted-form
  signing workflows remain source-gated and preview-only until authenticated
  point-of-use QA and completed signed-PDF visual QA are recorded.
- The authenticated platform-admin session verified that an account without an
  active brokerage membership cannot see restricted-form preview cards. This
  gate was preserved.

## Next required work

Run authenticated brokerage-admin QA with an active brokerage membership, then
complete the restricted-form preview and completed-signature gates one form at a
time. Do not infer brokerage membership or source authorization from a license
number or platform-admin role.
