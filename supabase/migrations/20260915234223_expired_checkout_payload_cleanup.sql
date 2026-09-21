-- Only the backend's signature-verified expired/unpaid event handler deletes
-- staging payloads. No browser read/write/delete grants or RLS policies.
grant delete on table public.hof_checkout_payloads to service_role;
