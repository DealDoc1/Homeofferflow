# Stripe lifecycle automated coverage — 2026-08-09

This companion record maps the repository's deterministic security suite to the
required Stripe lifecycle behaviors. It is code-level evidence only; it does
not replace a signed Stripe test delivery against the isolated branch.

## Verified automated behaviors

The bundled regression run completed with 657 tests passing. The following
tests in `tests/test_subscription_lifecycle_security.py` cover the lifecycle
contract:

| Runbook behavior | Automated assertion |
| --- | --- |
| Trial invoice keeps the subscription in `trialing` | `test_paid_trial_invoice_keeps_current_trialing_status` |
| Production rejects sandbox events | `test_stripe_test_mode_event_cannot_mutate_production_by_default`, `test_production_never_accepts_sandbox_events_even_if_the_flag_is_set` |
| Preview sharing the production database also rejects sandbox events | `test_preview_with_production_database_cannot_process_sandbox_events` |
| Explicitly isolated preview can process sandbox events | `test_isolated_test_environment_may_explicitly_process_sandbox_events` |
| Completed delivery is idempotent and does not store the event body | `test_webhook_ledger_deduplicates_completed_events_without_storing_event_body` |
| Failed deliveries can be retried | `test_webhook_ledger_records_processing_result_and_allows_failed_retry` |
| Ledger is server-only and admin monitoring is privacy-limited | `test_webhook_ledger_is_server_only`, `test_platform_admin_can_monitor_webhook_delivery_without_customer_or_payment_data` |
| Failed invoice produces `past_due` | `test_failed_invoice_immediately_marks_subscription_past_due` |
| Deleted subscription becomes `canceled` | `test_deleted_subscription_is_recorded_as_canceled` |
| Billing failure suspends an agent membership | `test_failed_invoice_suspends_agent_brokerage_membership` |
| Paid recovery restores billing suspension | `test_recovered_subscription_reactivates_existing_brokerage_membership`, `test_paid_invoice_restores_billing_suspended_membership` |
| Manual suspension is preserved | `test_recovered_subscription_does_not_undo_manual_broker_suspension` |
| Removed membership is preserved | `test_recovered_subscription_does_not_restore_removed_membership`, `test_billing_suspension_does_not_relabel_manual_or_removed_memberships` |
| Scheduled cancellation preserves access through the saved end date | `test_scheduled_cancellation_keeps_access_until_the_saved_end_date` |
| Non-active checkout does not create brokerage activation | `test_checkout_does_not_activate_brokerage_membership_for_a_non_active_subscription` |

## Still required for live completion

The isolated branch must still retain auditable intermediate database snapshots
from a real signed test-mode endpoint for trialing, scheduled cancellation,
past-due suspension, manual/removed preservation, duplicate delivery, and the
production rejection response. The endpoint and branch should be cleaned up
only after those snapshots are recorded.

