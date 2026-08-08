# Restricted TXR production gate smoke check - 2026-08-08

## Scope

This is a production security-boundary smoke check for the restricted TXR and
seller-disclosure preview routes. It confirms that an unauthenticated request
cannot reach private source or draft data. It does not claim authenticated
preview or completed-signature QA.

## Production checks

Origin: `https://www.homeofferflow.com`

| Request | Result |
|---|---|
| `GET /api/admin-dashboard?scope=approved_brokerage_sources` without a session | HTTP 401 with `A valid signed-in session is required.` |
| `GET /api/admin-dashboard` without a session | HTTP 401 with `A valid signed-in session is required.` |

## Local form checks

- Full regression suite: 516 tests passed.
- TXR signer geometry and TXR-1507 renderer tests passed.
- TXR-1501/1506/1507/1508 local unsigned rendering passed.
- Seller temporary lease completed-signature visual QA remains recorded separately.

## Gate status

The production boundary is fail-closed. Restricted TXR workflows remain
preview-only until authenticated point-of-use QA, document-specific signer-plan
confirmation, completed signed-PDF visual inspection, and release-authority
approval are recorded. This evidence intentionally does not enable signing.
