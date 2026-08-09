# Stripe lifecycle QA results — isolated branch — 2026-08-08

## Scope

This records the evidence currently present in the isolated Supabase branch
`stripe-lifecycle-qa` (`mtalxbxlutkuqcafjsac`). It does not claim that the full
runbook is complete; intermediate states that were not persisted as auditable
snapshots remain open.

## Isolation and schema evidence

- Runtime database URL: `https://mtalxbxlutkuqcafjsac.supabase.co`.
- Branch is distinct from the production project `acqylchftrjjoablvqyq`.
- Required tables and columns are present: `hof_subscriptions`,
  `hof_stripe_webhook_events`, `hof_brokerage_members`, `suspension_reason`,
  `trial_ends_at`, and `cancel_at_period_end`.
- The webhook ledger has server-only policy coverage in the branch.
- No production rows were queried or mutated by this QA verification.

## Ledger evidence

The branch contains 15 unique, processed `livemode=false` events. The event
types represented are:

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

The ledger contains no failed processing rows and no duplicate event IDs.

## Resulting state evidence

- The final isolated subscription row is `agent_starter_monthly` with status
  `active`, `cancel_at_period_end=false`, and a future `current_period_end`.
- The final isolated brokerage member is an `agent` with status `active` and
  `suspension_reason=null`, consistent with billing recovery restoring access.
- The observed event sequence demonstrates failure and subsequent paid-recovery
  deliveries, but the branch does not retain an intermediate snapshot proving
  the exact `past_due` membership suspension or the cancel-at-period-end state.

## Open items before declaring the runbook complete

1. Capture auditable intermediate snapshots for trialing, cancel-at-period-end,
   past-due billing suspension, manual suspension preservation, and deleted
   membership preservation.
2. Verify duplicate delivery behavior against the same event ID with a recorded
   single ledger row and unchanged subscription state.
3. Verify the production endpoint rejects one signed test-mode delivery without
   sending any additional test events to production.
4. Remove the test endpoint and pause/delete the isolated branch after the
   evidence packet is complete.

