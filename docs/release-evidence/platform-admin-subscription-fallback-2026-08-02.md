# Platform-admin subscription fallback evidence — 2026-08-02

## Scope

This change preserves internal HomeOfferFlow access for platform administrators when the browser cannot read a subscription row. It does not grant free access to brokerage administrators or agents.

## Implementation

- The browser subscription fallback derives a platform-admin flag from the existing platform-admin check.
- Platform admins receive the internal `free_admin` fallback only when the subscription query errors or returns no row.
- Brokerage administrators and agents continue to receive the normal inactive/trial/billing behavior.
- Existing active, canceled, or paid subscription rows remain authoritative.

## Verification

- Focused admin/OnDemand regression suite: 46 tests passed.
- Full repository test suite: 345 tests passed.
- PR: #71
- Merge commit: a999eedcfc45d9e29f5dc83e2e62c258542755b5

## Release state

The code is merged to `main`. It has not yet been promoted to the live Vercel production deployment because the project is operating under the Vercel Hobby deployment-cap policy and requires an explicit intentional-release approval.

No legal-form source, PDF mapping, offer-generation route, or completed-signature QA gate was changed.
