# Policy and launch-surface live audit — 2026-08-03

## Scope

This is a read-only production comparison of the public policy and OnDemand
launch surfaces against the checked-in files. No customer data, billing event,
offer packet, or restricted form workflow was created.

Production origin: `https://www.homeofferflow.com/`

Verified documents:

- `/terms.html`
- `/privacy.html`
- `/disclaimer.html`
- `/esign-consent.html`
- `/ondemand.html`

## Evidence

Each live response was fetched on 2026-08-03 and compared with its checked-in
counterpart using SHA-256. All five pairs matched exactly:

| Path | Result |
|---|---|
| `/terms.html` | Match |
| `/privacy.html` | Match |
| `/disclaimer.html` | Match |
| `/esign-consent.html` | Match |
| `/ondemand.html` | Match |

The live surfaces show the current product scope, including the 60-day
card-required OnDemand trial, $29/month renewal disclosure, cancellation
language, restricted-form source/authorization gates, AI educational
disclaimer, and the current limitation that standalone buyer-representation,
listing, and seller-disclosure workflows are not yet live.

## Release state

No runtime change was required. The current production deployment remains the
intentional release at commit `d9eb70b`, deployment
`dpl_9ouocpBidjaTrC7feae4UHHFEJzs` (READY). Documentation-only reconciliation
does not require another Vercel deployment.

