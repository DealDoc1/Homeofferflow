# Agent runtime trust-copy alignment

Date: 2026-09-22

## Finding

The canonical HTML correctly explained that an agent needs neither a brokerage seat nor payment to begin, and that recurring plan terms appear before checkout. The progressive-focus script then replaced that note after page load with older, less-complete wording.

## Change

- Preserved the complete no-seat, no-payment, and before-checkout explanation after the progressive-focus script runs.
- Kept the optional guide shelf collapsed so Question 1 remains the primary action.
- Added the already approved privacy-safe `site_recovery` channel to the focus script so recovery attribution is not downgraded after page load.

## Verification

- Static regression coverage now checks both the canonical HTML and the post-load script copy.
- Focused agent-landing, recovery, public-discovery, and technical-SEO tests pass.
- Production browser inspection supplied the failure evidence; this correction is queued for the next bundled deployment to avoid an unnecessary additional Vercel release.
