# Stripe lifecycle QA branch health evidence

Date: 2026-08-08

## Scope

Disposable Supabase branch used for non-production Stripe lifecycle QA:

- Branch: `stripe-lifecycle-qa`
- Project ref: `mtalxbxlutkuqcafjsac`
- Parent project: `acqylchftrjjoablvqyq`
- Branch status: `FUNCTIONS_DEPLOYED`
- Preview project status: `ACTIVE_HEALTHY`

## Recovery performed

The first branch replay stopped at the product tracker migration because the remote schema baseline already contained `hof_qa_runs` without the composite uniqueness constraint required by the seed upsert. The repository migration now creates that index idempotently:

`hof_qa_runs_scenario_release_environment_key` on `(scenario_id, release_name, environment)`.

The disposable branch was reset to the baseline and replayed with a branch-only migration named `homeofferflow_tracker_replay_fix`. The branch migration history now contains the baseline plus that replay fix, and the index is present.

## Verification

- `hof_subscriptions` exists on the isolated branch.
- `hof_stripe_webhook_events` exists on the isolated branch.
- `hof_qa_runs_scenario_release_environment_key` exists on the isolated branch.
- Full local suite: `513` tests, `OK`.
- TXR signer geometry guards: passing.
- Production code and production Supabase project were not reset or modified.

## Release gate

This evidence establishes isolated branch health. It does not authorize connecting Stripe test events to production. Stripe lifecycle delivery still requires the non-production webhook endpoint and the runbook's end-to-end event sequence.
