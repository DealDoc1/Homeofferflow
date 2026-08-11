-- Operational telemetry must not retain raw SignWell webhook bodies. Existing
-- unmatched events are preserved for incident counts/timing, while their
-- provider payload and free-form message are replaced with a compact marker.
-- This exact predicate targets the 12 historical rows that contain raw data;
-- it does not alter future aggregate-only telemetry.
update public.hof_offer_events
set
  message = 'Historical SignWell webhook lifecycle event retained with sensitive payload redacted.',
  metadata = jsonb_build_object(
    'source', 'signwell-webhook',
    'redacted', true,
    'redaction_reason', 'raw_provider_payload'
  )
where event_type = 'signwell_webhook_unmatched'
  and metadata ? 'raw';
