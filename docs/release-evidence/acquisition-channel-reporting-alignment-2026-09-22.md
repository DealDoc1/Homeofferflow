# Acquisition channel reporting alignment

Date: 2026-09-22

## Finding

The public APIs accepted privacy-safe acquisition channels that the admin conversion summaries did not enumerate. As a result, valid homepage, receipt, outreach, and owned-directory events could be stored and included in total counts while remaining absent from the per-channel breakdown. The partner guide also labeled traffic from the owned provider directory as organic after page load.

## Change

- Aligned partner, agent, investor, and seller admin channel breakdowns with the channels accepted by their public event endpoints.
- Preserved homepage and partner-receipt attribution when the partner landing page records a post-load guide expansion.
- Preserved owned-directory attribution when a provider-directory visitor opens the partner placement guide.
- Expanded partner directory empty-result reporting to cover every accepted privacy-safe partner channel.
- Added a contract test that fails if backend channel acceptance and admin reporting diverge again.

## Verification

- 105 focused acquisition, partner, seller, agent, and investor tests pass.
- JavaScript syntax checks pass for both changed runtime assets.
- The complete local suite ran 2,427 tests: 2,426 passed; one unrelated cross-language assumption-checkout test remains environment-sensitive locally and returns the existing fail-closed 503 response. No assumption-checkout or packet files changed.
- The correction is queued for the next bundled production deployment to avoid an unnecessary standalone Vercel release.
