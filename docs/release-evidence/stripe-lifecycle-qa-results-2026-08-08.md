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

## Current branch reconciliation — 2026-09-10

The isolated branch was rechecked directly, without reading or changing
production data. Its compact migration history is expected for a branch based
on the schema baseline; direct schema inspection confirms the lifecycle tables
and fields required by the current webhook are present.

- `hof_subscriptions`, `hof_stripe_webhook_events`, and
  `hof_brokerage_members` exist.
- The branch has `trial_ends_at`, `cancel_at_period_end`, and
  `suspension_reason` fields.
- Unique indexes exist for `hof_subscriptions.user_id` and
  `hof_stripe_webhook_events.stripe_event_id`.
- The ledger contains 35 distinct processed sandbox event IDs across Checkout,
  subscription create/update/delete, paid, successful-payment, and failed-
  payment event types. It has no non-processed rows.
- The final aggregate state is one active and one canceled subscription, plus
  one active and one removed membership. These final states are consistent with
  recovery and removed-membership preservation, but do **not** replace
  checkpoint evidence of the intermediate trialing, scheduled-cancellation,
  past-due, and manual-suspension states.

The local Stripe CLI route in `docs/STRIPE_LIFECYCLE_QA.md` is now the
preferred way to capture those remaining checkpoints without paying for a
Vercel preview deployment.
