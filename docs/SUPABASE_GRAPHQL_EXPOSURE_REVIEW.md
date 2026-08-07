# Supabase GraphQL exposure review

Updated: 2026-08-07

## Decision

Do not revoke `authenticated` access broadly or drop `pg_graphql`. The current
browser application intentionally uses Supabase's authenticated Data API
directly for several signed-in workflows. A blanket revoke would break offer
creation, profiles, subscriptions, brokerage setup, agent documents, and
addenda/source workflows. Usage telemetry is the first dependency moved behind
an authenticated server action; its server-only privilege migration was
applied on 2026-08-07 after the runtime/server tests passed. A live ACL
check confirmed direct browser access is denied while service-role writes are
retained.

The Supabase advisor warning `0027_pg_graphql_authenticated_table_exposed` is
therefore tracked as a reviewed warning, not an unreviewed vulnerability. RLS
and table grants remain the actual authorization boundary; GraphQL schema
visibility is a separate concern.

## Authentication hardening

On 2026-08-07, Supabase Pro's Email-provider setting **Prevent use of leaked
passwords** was enabled for the HomeOfferFlow production project. A follow-up
security-advisor check no longer reports `auth_leaked_password_protection`.

## Evidence reviewed

The production code directly calls these tables from `index.html` or a
server-side API route:

| Table | Current dependency | Release decision |
| --- | --- | --- |
| `hof_offers` | Signed-in offer create/read/update and server webhooks | Keep authenticated Data API; owner RLS remains required |
| `hof_offer_events` | Signed-in offer status/timeline reads; server writes | Keep current access until timeline reads move behind an API |
| `hof_profiles` | Profile and brokerage setup/read | Keep authenticated access; owner/broker policies are required |
| `hof_subscriptions` | Signed-in entitlement reads; server lifecycle writes | Keep authenticated select only; no browser insert/update |
| `hof_usage_events` | Usage summary and signed-packet events now route through `/api/submit-feedback` server actions | Server-only migration applied; RLS remains enabled, no public/authenticated table grants or policies remain, and service-role writes are retained |
| `hof_brokerages` | Signed-in brokerage setup and branding | Keep authenticated access with membership/admin RLS |
| `hof_brokerage_members` | Signed-in roster/association reads | Keep authenticated select with brokerage membership RLS |
| `hof_agent_documents` | Agent IABS/document profile storage metadata | Keep authenticated owner-scoped access |
| `hof_brokerage_form_sources` | Broker-admin source workflow | Keep authenticated access with broker-admin policy and source gates |
| `hof_listing_workspaces` | Signed-in seller/listing workspace workflow | Keep authenticated access with brokerage membership RLS |
| `hof_seller_leads` | Seller lead/listing intake workflow | Keep current signed-in workflow; review before server migration |
| `hof_ai_offer_reviews` | AI review snapshots now save through `/api/ai-offer-review` with `action=save_snapshot` | Authenticated and anonymous table grants are revoked; the server verifies the session and supplies `user_id` |
| `hof_feedback` | Feedback submission and platform-admin feed are server-routed | Authenticated and anonymous table grants are revoked; service-role routes remain |
| `hof_standalone_agreements` | Signed-in agreement workflow | Keep until signer/offer access is moved behind an API |

The legacy tables listed in
`supabase/homeofferflow_legacy_table_access_hardening.sql` are not current
browser dependencies and remain revoked for both `anon` and `authenticated`.

## Next hardening sequence

1. Keep the current RLS/grant tests in CI and verify the live advisor after
   every schema release.
2. Move one sensitive browser dependency at a time behind a server endpoint.
   Usage telemetry is now routed through `/api/submit-feedback`; feedback and
   AI review snapshots are already server-only under their respective SQL files.
3. After browser reads/writes are removed and live end-to-end tests pass,
   revoke `authenticated` table privileges for that relation and verify both
   the API path and direct-browser denial. This is complete for
   `hof_usage_events` as of 2026-08-07.
4. Revisit disabling `pg_graphql` only after confirming no production or
   support workflow uses it.

## Do not do

- Do not apply a blanket `revoke all ... from authenticated` migration. The
  table-specific usage migration is now applied only to `hof_usage_events`.
- Do not expose service-role credentials to the browser.
- Do not treat the advisor warning alone as proof that customer data is
  readable; verify RLS and grants together.
- Do not deploy this documentation-only review as a Vercel preview while the
  Hobby deployment cap is constrained. Bundle it with the next intentional
  release.
