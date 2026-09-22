# Homebuyer channel reporting completion

Date: 2026-09-22

## Finding

The public homebuyer event endpoint and buyer landing page both accepted and recorded the privacy-safe `homepage` channel, but the admin homebuyer channel breakdown omitted it. Homepage buyer traffic therefore appeared in the overall funnel totals without appearing in the corresponding channel view and workspace-start report.

## Change

- Added homepage traffic to the homebuyer admin channel breakdown.
- Expanded the shared acquisition-channel contract test to cover both the homebuyer and OnDemand reporting contracts in addition to partner, agent, investor, and seller paths.

## Verification

- The acquisition reporting contract suite confirms that every accepted backend channel is represented in its admin breakdown.
- The focused homebuyer funnel and acquisition reporting tests pass.
- No customer intake, checkout, form, payment, or deployment behavior changed.
- The correction is queued for the next intentional production bundle.
