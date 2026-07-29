-- HomeOfferFlow product roadmap, QA, and release tracker.
-- Applied to Supabase project acqylchftrjjoablvqyq on 2026-07-21.

create extension if not exists pgcrypto;
create schema if not exists private;

create or replace function private.hof_set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

revoke all on function private.hof_set_updated_at() from public, anon, authenticated;

create table if not exists public.hof_platform_admins (
  user_id uuid primary key references auth.users(id) on delete cascade,
  label text,
  created_at timestamptz not null default now()
);

alter table public.hof_platform_admins enable row level security;
revoke all on table public.hof_platform_admins from anon, authenticated;
grant all on table public.hof_platform_admins to service_role;

drop policy if exists "platform_admins_server_only" on public.hof_platform_admins;
create policy "platform_admins_server_only"
on public.hof_platform_admins
for all
to authenticated
using (false)
with check (false);

insert into public.hof_platform_admins (user_id, label)
select id, coalesce(email, 'HomeOfferFlow administrator')
from auth.users
where lower(email) in ('andrewchri@gmail.com', 'andrew@ondemanddfw.com', 'support@homeofferflow.com')
on conflict (user_id) do update set label = excluded.label;

alter table public.hof_roadmap_items
  add column if not exists slug text,
  add column if not exists environment text not null default 'backlog',
  add column if not exists qa_status text not null default 'not_tested',
  add column if not exists target_release text,
  add column if not exists current_release text,
  add column if not exists known_issues text,
  add column if not exists next_action text,
  add column if not exists github_ref text,
  add column if not exists requested_by text not null default 'Andrew Christian',
  add column if not exists is_locked boolean not null default false,
  add column if not exists metadata jsonb not null default '{}'::jsonb,
  add column if not exists updated_at timestamptz not null default now(),
  add column if not exists completed_at timestamptz;

update public.hof_roadmap_items
set slug = case lower(title)
  when 'texas trec july 2026 form updates' then 'trec-20-19-buyer-offer'
  when 'signwell status tracking' then 'signwell-status-tracking'
  when 'brokerage branding' then 'brokerage-branding'
  when 'brokerage admin dashboard' then 'broker-dashboard'
  when 'ai offer review' then 'ai-offer-competitiveness'
  when 'fsbo seller intake' then 'fsbo-workflow'
  when 'title partner placement' then 'partner-marketplace'
  when 'state expansion architecture' then 'state-expansion'
  else 'legacy-' || id::text
end
where slug is null;

create unique index if not exists hof_roadmap_items_slug_key
  on public.hof_roadmap_items(slug);
create index if not exists hof_roadmap_items_status_priority_idx
  on public.hof_roadmap_items(status, priority);

drop trigger if exists hof_roadmap_items_set_updated_at on public.hof_roadmap_items;
create trigger hof_roadmap_items_set_updated_at
before update on public.hof_roadmap_items
for each row execute function private.hof_set_updated_at();

alter table public.hof_roadmap_items enable row level security;
revoke all on table public.hof_roadmap_items from anon, authenticated;
grant all on table public.hof_roadmap_items to service_role;

drop policy if exists "hof_roadmap_items_select_auth" on public.hof_roadmap_items;
drop policy if exists "roadmap_server_only" on public.hof_roadmap_items;
create policy "roadmap_server_only"
on public.hof_roadmap_items
for all
to authenticated
using (false)
with check (false);

create table if not exists public.hof_qa_scenarios (
  id uuid primary key default gen_random_uuid(),
  scenario_key text not null unique,
  title text not null,
  category text not null,
  description text,
  payload_name text,
  expected_pages integer check (expected_pages is null or expected_pages > 0),
  priority integer not null default 999,
  active boolean not null default true,
  current_status text not null default 'not_tested'
    check (current_status in ('not_tested', 'partial', 'passed', 'failed', 'blocked', 'staging_passed', 'production')),
  last_verified_release text,
  last_verified_at timestamptz,
  coverage jsonb not null default '{}'::jsonb,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hof_releases (
  id uuid primary key default gen_random_uuid(),
  release_key text not null unique,
  title text not null,
  environment text not null default 'staging'
    check (environment in ('local', 'staging', 'production')),
  status text not null default 'planned'
    check (status in ('planned', 'in_progress', 'qa', 'staging_passed', 'deployed', 'rolled_back', 'blocked')),
  qa_status text not null default 'not_tested'
    check (qa_status in ('not_tested', 'partial', 'passed', 'failed', 'blocked')),
  git_branch text,
  commit_sha text,
  github_pr text,
  vercel_deployment_url text,
  summary text,
  known_issues text,
  next_action text,
  approved_by text,
  approved_at timestamptz,
  deployed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hof_qa_runs (
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references public.hof_qa_scenarios(id) on delete cascade,
  release_id uuid references public.hof_releases(id) on delete set null,
  release_name text not null,
  environment text not null default 'staging'
    check (environment in ('local', 'staging', 'production')),
  status text not null default 'queued'
    check (status in ('queued', 'running', 'passed', 'failed', 'blocked')),
  packet_name text,
  evidence_ref text,
  git_commit text,
  github_pr text,
  executed_by uuid references auth.users(id) on delete set null,
  started_at timestamptz,
  completed_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  unique (scenario_id, release_name, environment)
);

create table if not exists public.hof_qa_results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.hof_qa_runs(id) on delete cascade,
  page_number integer check (page_number is null or page_number > 0),
  section text,
  field_name text not null,
  expected text,
  actual text,
  status text not null default 'not_tested'
    check (status in ('pass', 'fail', 'watch', 'not_tested', 'not_applicable')),
  coordinate_locked boolean not null default false,
  proposed_change text,
  reviewer_notes text,
  created_at timestamptz not null default now()
);

create index if not exists hof_qa_scenarios_status_priority_idx
  on public.hof_qa_scenarios(current_status, priority);
create index if not exists hof_qa_runs_scenario_created_idx
  on public.hof_qa_runs(scenario_id, created_at desc);
create index if not exists hof_qa_runs_release_id_idx
  on public.hof_qa_runs(release_id);
create index if not exists hof_qa_runs_executed_by_idx
  on public.hof_qa_runs(executed_by);
create index if not exists hof_qa_results_run_page_idx
  on public.hof_qa_results(run_id, page_number);
create index if not exists hof_releases_status_created_idx
  on public.hof_releases(status, created_at desc);

drop trigger if exists hof_qa_scenarios_set_updated_at on public.hof_qa_scenarios;
create trigger hof_qa_scenarios_set_updated_at
before update on public.hof_qa_scenarios
for each row execute function private.hof_set_updated_at();

drop trigger if exists hof_releases_set_updated_at on public.hof_releases;
create trigger hof_releases_set_updated_at
before update on public.hof_releases
for each row execute function private.hof_set_updated_at();

alter table public.hof_qa_scenarios enable row level security;
alter table public.hof_qa_runs enable row level security;
alter table public.hof_qa_results enable row level security;
alter table public.hof_releases enable row level security;

revoke all on table public.hof_qa_scenarios, public.hof_qa_runs, public.hof_qa_results, public.hof_releases from anon, authenticated;
grant all on table public.hof_qa_scenarios, public.hof_qa_runs, public.hof_qa_results, public.hof_releases to service_role;

drop policy if exists "qa_scenarios_server_only" on public.hof_qa_scenarios;
create policy "qa_scenarios_server_only" on public.hof_qa_scenarios
for all to authenticated using (false) with check (false);

drop policy if exists "qa_runs_server_only" on public.hof_qa_runs;
create policy "qa_runs_server_only" on public.hof_qa_runs
for all to authenticated using (false) with check (false);

drop policy if exists "qa_results_server_only" on public.hof_qa_results;
create policy "qa_results_server_only" on public.hof_qa_results
for all to authenticated using (false) with check (false);

drop policy if exists "releases_server_only" on public.hof_releases;
create policy "releases_server_only" on public.hof_releases
for all to authenticated using (false) with check (false);

insert into public.hof_roadmap_items
  (slug, category, title, description, priority, status, environment, qa_status, target_release, current_release, known_issues, next_action, github_ref, is_locked, metadata)
values
  ('trec-20-19-buyer-offer', 'Forms', 'TREC 20-19 buyer offer workflow', 'Controlled production launch of the July 2026 Texas one-to-four family contract and verified buyer packet paths.', 1, 'production', 'production', 'passed', null, 'Controlled 20-19 launch', null, 'Continue gated expansion without moving locked coordinates.', 'PR #4', true, '{"coverage":"cash, conventional, FHA, VA, USDA and ten golden scenarios"}'),
  ('seller-temporary-lease', 'Forms', 'Seller Temporary Residential Lease', 'Support TREC 15-7 when the seller remains temporarily after closing.', 2, 'production', 'production', 'passed', null, 'Seller Temporary Lease production release 071b773', null, 'Keep TREC 15-7 in packet regressions; do not change verified coordinates without fresh rendered-PDF QA.', '071b773', true, '{"form":"TREC 15-7","packet_pages":14}'),
  ('txr-1507-short-buyer-tenant-representation', 'Forms', 'TXR-1507 Residential Buyer/Tenant Representation Agreement - Short Form', 'Agent-selected Texas REALTORS® buyer or tenant representation agreement with dedicated signing and visual QA.', 3, 'planned', 'backlog', 'not_tested', 'Buyer relationship release', null, 'The form source has been reviewed; workflow, authorization gate, signatures, and rendered QA are not implemented.', 'Obtain an OnDemand-approved TXR-1507 source, then build the agent-selected short-form workflow and completed-signature QA.', null, false, '{"form":"TXR-1507","revision":"06-15-26","pages":2,"source_authorization":"Texas REALTORS member form"}'),
  ('txr-1501-long-buyer-tenant-representation', 'Forms', 'TXR-1501 Residential Buyer/Tenant Representation Agreement - Long Form', 'Agent-selected Texas REALTORS® long-form buyer or tenant representation agreement with its own mapping and visual QA.', 4, 'planned', 'backlog', 'not_tested', 'Buyer relationship release', null, 'The form source has been reviewed; no workflow or field mapping is implemented.', 'Build only after the Short Form is released; never silently substitute this form for the Short Form.', null, false, '{"form":"TXR-1501","revision":"06-15-26","pages":6,"source_authorization":"Texas REALTORS member form"}'),
  ('txr-1508-unrepresented-showing', 'Forms', 'TXR-1508 Unrepresented Customer Showing Form', 'Separate limited no-representation showing workflow for agents who choose that path.', 5, 'planned', 'backlog', 'not_tested', 'Buyer relationship release', null, 'The form source has been reviewed; no workflow or signature plan is implemented.', 'Build after representation agreement workflows; preserve its no-representation scope.', null, false, '{"form":"TXR-1508","revision":"02-25-26","pages":1,"source_authorization":"Texas REALTORS member form"}'),
  ('txr-1506-general-information-notice', 'Forms', 'TXR-1506 General Information and Notice to Consumers', 'Standalone Texas REALTORS® consumer notice and acknowledgement workflow.', 6, 'planned', 'backlog', 'not_tested', 'Buyer relationship release', null, 'The form source has been reviewed; no workflow or signature plan is implemented.', 'Build as a separate acknowledgement workflow, not an automatic offer-packet attachment.', null, false, '{"form":"TXR-1506","revision":"06-15-26","pages":6,"source_authorization":"Texas REALTORS member form"}'),
  ('seller-financing', 'Forms', 'Seller Financing', 'Targeted mapping, attachment, signature, and fail-closed QA for the Seller Financing Addendum.', 3, 'blocked', 'backlog', 'not_tested', 'Targeted forms release', null, 'Not approved for production.', 'Build a dedicated payload and visually inspect every applicable blank and checkbox.', null, false, '{}'),
  ('loan-assumption', 'Forms', 'Loan Assumption', 'Targeted mapping, attachment, signature, and fail-closed QA for loan assumption.', 4, 'blocked', 'backlog', 'not_tested', 'Targeted forms release', null, 'Not approved for production.', 'Build a dedicated payload and visually inspect every applicable blank and checkbox.', null, false, '{}'),
  ('paragraph4-residential-lease', 'Forms', 'Paragraph 4 Residential Lease path', 'Support the Paragraph 4 residential lease checkbox and required attachment.', 5, 'blocked', 'backlog', 'not_tested', 'Targeted leases release', null, 'Production intentionally fails closed.', 'Add the correct promulgated form, payload, mapping, signatures, and rendered QA.', 'PR #7 safety gate', false, '{}'),
  ('paragraph4-fixture-lease', 'Forms', 'Paragraph 4 Fixture Lease path', 'Support the Paragraph 4 fixture lease checkbox and required attachment.', 6, 'blocked', 'backlog', 'not_tested', 'Targeted leases release', null, 'Production intentionally fails closed.', 'Add the correct form, payload, mapping, signatures, and rendered QA.', 'PR #7 safety gate', false, '{}'),
  ('paragraph4-natural-resource-lease', 'Forms', 'Paragraph 4 Natural Resource Lease path', 'Support the Paragraph 4 natural resource lease checkbox and required attachment.', 7, 'blocked', 'backlog', 'not_tested', 'Targeted leases release', null, 'Production intentionally fails closed.', 'Add the correct form, payload, mapping, signatures, and rendered QA.', 'PR #7 safety gate', false, '{}'),
  ('buyer-temporary-lease', 'Forms', 'Buyer Temporary Residential Lease', 'Attach and sign the Buyer Temporary Residential Lease when possession requires it.', 8, 'production', 'production', 'passed', null, 'PR #8', null, 'Regression-test with the golden suite after related packet assembly changes.', 'PR #8', true, '{}'),
  ('hydrostatic-addendum', 'Forms', 'Hydrostatic Testing Addendum', 'Add, map, sign, and test the hydrostatic testing form.', 9, 'blocked', 'backlog', 'not_tested', 'Additional forms release', null, 'Unsupported in production.', 'Obtain the correct form and create a targeted payload.', null, false, '{}'),
  ('environmental-assessment-addendum', 'Forms', 'Environmental Assessment Addendum', 'Add, map, sign, and test the environmental assessment form.', 10, 'blocked', 'backlog', 'not_tested', 'Additional forms release', null, 'Unsupported in production.', 'Obtain the correct form and create a targeted payload.', null, false, '{}'),
  ('mineral-reservation-addendum', 'Forms', 'Mineral Reservation Addendum', 'Add, map, sign, and test the mineral reservation form.', 11, 'blocked', 'backlog', 'not_tested', 'Additional forms release', null, 'Unsupported in production.', 'Obtain the correct form and create a targeted payload.', null, false, '{}'),
  ('seller-disclosure-uploads', 'Seller Side', 'Seller and listing disclosure uploads', 'Allow seller/listing disclosures to be included as uploaded PDFs without incorrectly generating seller forms in the buyer workflow.', 12, 'production', 'production', 'partial', null, 'Controlled production launch', 'Full seller-side generation remains separate.', 'Preserve upload support while building the seller workflow.', null, true, '{}'),
  ('agent-dashboard', 'Platform', 'Agent Dashboard', 'Authentication, drafts, saved offers, resume, duplicate, delete, SignWell status, profile, and usage.', 20, 'in_progress', 'production', 'partial', 'Platform hardening', 'Beta foundation', 'Needs production hardening and deeper reporting.', 'Finish operational metrics, reliability states, and regression coverage.', null, false, '{}'),
  ('broker-dashboard', 'Brokerage', 'Broker Dashboard', 'Brokerage-wide agent, offer, usage, compliance, and partner reporting.', 21, 'in_progress', 'production', 'partial', 'Brokerage release', 'Foundation', 'Agent management and brokerage reporting are incomplete.', 'Add agent membership management and brokerage-level offer/usage views.', null, false, '{}'),
  ('ai-offer-competitiveness', 'AI', 'AI Offer Competitiveness Review', 'Offer score, risk checklist, strengths, and strategy suggestions with rules fallback.', 22, 'in_progress', 'production', 'partial', 'AI validation release', 'Beta foundation', 'Needs calibration and production validation.', 'Create benchmark offers and compare model output against expert review.', null, false, '{}'),
  ('fsbo-workflow', 'Seller Side', 'FSBO workflow', 'Seller intake, package interest, partner needs, checkout, packet preparation, and transaction support.', 23, 'in_progress', 'production', 'partial', 'Seller platform release', 'Lead-capture foundation', 'Checkout and full transaction workflow are incomplete.', 'Convert selected seller packages from intake into supported fulfillment flows.', null, false, '{}'),
  ('seller-workflow', 'Seller Side', 'Full seller workflow', 'Seller-side disclosures, forms, packet generation, checkout, and transaction management.', 24, 'planned', 'backlog', 'not_tested', 'Seller platform release', null, 'Only intake and selected addendum work exist.', 'Define the seller packet catalog and first golden seller scenarios.', null, false, '{}'),
  ('admin-dashboard', 'Platform', 'Admin Dashboard', 'Operational metrics for offers, events, subscriptions, brokerages, releases, roadmap, and QA.', 25, 'in_progress', 'production', 'partial', 'Operations release', 'Beta foundation', 'Needs hardened authorization and tracker views.', 'Use the Supabase tracker as the dashboard source of truth.', null, false, '{}'),
  ('founding-partner-pilot', 'Partners', 'Founding Partner Pilot', 'Three-tier partner advertising offer with category-and-market pricing, explicit placement inventory, neutral provider selection, public intake, and campaign attribution.', 26, 'in_progress', 'staging', 'partial', 'Founding Partner Revenue Pilot v2', 'Core Partner ($149), Featured Partner ($399), and Premier Partner ($799) sales tiers prepared for preview.', 'Preview approval, commercial agreement review, and first qualified partner sale are still required.', 'Verify the tier selector and lead capture in preview, approve the rate card, and begin category-by-category founder outreach.', null, false, '{"monetization_stage":"demand_validation","no_volume_promise":true,"flat_monthly_advertising":true,"neutral_provider_selector":true,"tier_rates":{"core_partner":149,"featured_partner":399,"premier_partner":799}}'),
  ('partner-marketplace', 'Partners', 'Partner Marketplace', 'Partner placements, onboarding, billing, market routing, and click reporting.', 26, 'in_progress', 'production', 'partial', 'Partner release', 'Foundation', 'Onboarding, billing, and click reporting are incomplete.', 'Add partner lifecycle and attribution reporting.', null, false, '{}'),
  ('team-support', 'Brokerage', 'Team support', 'Brokerage membership, invitations, roles, permissions, defaults, and reporting.', 27, 'in_progress', 'production', 'partial', 'Brokerage release', 'Data foundation', 'End-user membership administration is incomplete.', 'Finish invitations, removals, role controls, and team reporting.', null, false, '{}'),
  ('brokerage-branding', 'Brokerage', 'Brokerage branding', 'Logo, colors, disclaimer, contact information, and form/email defaults.', 28, 'in_progress', 'production', 'partial', 'Brokerage release', 'Foundation', 'Direct logo upload is not implemented.', 'Add Supabase Storage logo upload and propagate branding into packets and emails.', null, false, '{}'),
  ('subscription-usage-management', 'Billing', 'Subscription and usage management', 'Stripe-backed plans, packet limits, billing portal, usage events, and account status.', 29, 'in_progress', 'production', 'partial', 'Billing hardening', 'Foundation', 'Needs complete lifecycle and operational QA.', 'Add renewal, cancellation, limit, and failed-payment regression coverage.', null, false, '{}'),
  ('signwell-status-tracking', 'Signing', 'SignWell status tracking', 'Track awaiting signature, partially signed, and fully executed document status.', 30, 'production', 'production', 'passed', null, 'Production foundation', null, 'Continue webhook and status-refresh monitoring.', null, true, '{}'),
  ('automated-visual-regression', 'QA', 'Automated rendered-PDF regression', 'Compare rendered golden packet pages and field regions after every mapping or assembly change.', 31, 'planned', 'backlog', 'not_tested', 'QA automation release', null, 'Current rendered review is manual.', 'Build image-based page comparison with approved baselines and field-region tolerances.', null, false, '{}'),
  ('production-deployment-checklist', 'Operations', 'Production deployment checklist', 'One authoritative gate covering tests, signed packet QA, PR, preview, production, monitoring, and rollback.', 32, 'in_progress', 'production', 'partial', 'Operations release', 'Distributed process', 'The old QA ledger header is stale.', 'Consolidate the current production truth and gate criteria.', null, false, '{}'),
  ('supabase-product-tracker', 'Operations', 'Supabase product and QA tracker', 'Authoritative enhancement, QA scenario, field-result, and release-gate tracking in the Admin Dashboard.', 33, 'in_progress', 'production', 'partial', 'Admin tracker release', 'Database live; dashboard branch prepared', 'Dashboard/API changes are not yet published to GitHub.', 'Publish agent/supabase-product-tracker and verify the authenticated Admin Dashboard.', null, false, '{}'),
  ('seo-hero-update', 'Marketing', 'SEO hero update', 'Use the approved plain-English Texas offer positioning and avoid legal guarantees.', 34, 'production', 'production', 'passed', null, 'Launch messaging production release 57f768d', null, 'Monitor launch conversion and keep the Texas offer scope wording current as new agent forms are approved.', '57f768d', true, '{}'),
  ('additional-texas-forms', 'Forms', 'Additional Texas promulgated forms', 'Expand the verified form catalog through isolated, fail-closed releases.', 35, 'in_progress', 'staging', 'partial', 'Ongoing', 'Controlled expansion', 'Several optional forms remain blocked.', 'Unlock one targeted form only after full blank, checkbox, attachment, and signature QA.', null, false, '{}'),
  ('state-expansion', 'Expansion', 'State expansion architecture', 'Prepare form configuration and product architecture for Arizona and additional states.', 90, 'deferred', 'backlog', 'not_tested', 'Post-Texas roadmap', null, 'Texas coverage is still being completed.', 'Resume after the Texas buyer and seller workflows are stable.', null, false, '{}')
on conflict (slug) do update set
  category = excluded.category,
  title = excluded.title,
  description = excluded.description,
  priority = excluded.priority,
  status = excluded.status,
  environment = excluded.environment,
  qa_status = excluded.qa_status,
  target_release = excluded.target_release,
  current_release = excluded.current_release,
  known_issues = excluded.known_issues,
  next_action = excluded.next_action,
  github_ref = excluded.github_ref,
  is_locked = excluded.is_locked,
  metadata = excluded.metadata,
  updated_at = now();

insert into public.hof_qa_scenarios
  (scenario_key, title, category, description, payload_name, priority, current_status, last_verified_release, coverage, notes)
values
  ('golden-01-cash-one-buyer-no-agent', 'Cash / one buyer / no agent', 'Golden Packet', 'Minimal cash packet with one buyer, no agent, no HOA, and no addenda.', 'Golden scenario 1', 1, 'passed', '18B', '{"buyer_count":1,"financing":"cash","buyer_agent":false,"hoa":false,"addenda":"none"}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-02-cash-two-buyers-no-agent', 'Cash / two buyers / no agent', 'Golden Packet', 'Cash packet with two buyers and no buyer agent.', 'Golden scenario 2', 2, 'passed', '18B', '{"buyer_count":2,"financing":"cash","buyer_agent":false}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-03-conventional-one-buyer-agent', 'Conventional / one buyer / buyer agent', 'Golden Packet', 'Conventional financing with one buyer and buyer-agent information.', 'Golden scenario 3', 3, 'passed', '18B', '{"buyer_count":1,"financing":"conventional","buyer_agent":true}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-04-conventional-two-buyers-repairs', 'Conventional / two buyers / repairs', 'Golden Packet', 'Two buyers with repairs, warranty, and seller concession.', 'Golden scenario 4', 4, 'passed', '18B', '{"buyer_count":2,"financing":"conventional","repairs":true,"warranty":true,"concession":true}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-05-financing-hoa', 'Financing plus HOA', 'Golden Packet', 'Financed offer with mandatory HOA membership and the HOA addendum.', 'Golden scenario 5', 5, 'passed', '18B', '{"financing":"conventional","hoa":true}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-06-financing-appraisal', 'Financing plus appraisal', 'Golden Packet', 'Financed offer with the appraisal addendum.', 'Golden scenario 6', 6, 'passed', '18B', '{"financing":"conventional","appraisal":true}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-07-financing-sale-contingency', 'Financing plus sale contingency', 'Golden Packet', 'Financed offer with Sale of Other Property.', 'Golden scenario 7', 7, 'passed', '18B', '{"financing":"conventional","sale_contingency":true}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-08-financing-backup', 'Financing plus Backup Contract', 'Golden Packet', 'Financed offer with the Backup Contract Addendum.', 'Golden scenario 8', 8, 'passed', '18B', '{"financing":"conventional","backup":true}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-09-supported-addenda-stress', 'Supported addenda stress packet', 'Golden Packet', 'All supported buyer addenda in one regression packet.', 'Golden scenario 9', 9, 'passed', '18B', '{"stress_packet":true,"all_supported_addenda":true}', 'Rendered PDF reviewed field-by-field.'),
  ('golden-10-sparse-edge-case', 'Sparse optional-field edge case', 'Golden Packet', 'Sparse packet with optional inputs left blank.', 'Golden scenario 10', 10, 'passed', '18B', '{"sparse":true}', 'Rendered PDF reviewed field-by-field.'),
  ('target-fha', 'FHA financing', 'Targeted Financing', 'Verify FHA checkbox, financing addendum fields, and signatures.', 'FHA targeted payload', 20, 'passed', '18B', '{"financing":"fha"}', 'Approved for the controlled production gate.'),
  ('target-va', 'VA financing', 'Targeted Financing', 'Verify VA checkbox, financing addendum fields, and signatures.', 'VA targeted payload', 21, 'passed', '18B', '{"financing":"va"}', 'Approved for the controlled production gate.'),
  ('target-usda', 'USDA financing', 'Targeted Financing', 'Verify USDA checkbox and all financing-addendum blanks.', 'USDA targeted payload', 22, 'passed', '18B', '{"financing":"usda"}', 'Coordinates corrected from enlarged screenshot review and approved.'),
  ('target-12b-percentage', 'Paragraph 12B percentage compensation', 'Targeted Contract', 'Verify seller-paid and buyer-paid percentage paths.', '12B percentage payload', 23, 'production', 'PR #6', '{"paragraph":"12B","compensation_type":"percentage"}', 'Merged and production-enabled.'),
  ('target-buyer-temporary-lease', 'Buyer Temporary Residential Lease', 'Targeted Addendum', 'Verify checkbox, packet assembly, every applicable blank, and signatures.', 'Buyer temporary lease payload', 24, 'production', 'PR #8', '{"form":"TREC 16-7"}', 'Merged and production-enabled.'),
  ('target-seller-temporary-lease', 'Seller Temporary Residential Lease', 'Targeted Addendum', 'Verify checkbox, packet assembly, every applicable blank, and signatures.', 'Seller temporary lease payload', 25, 'production', '071b773', '{"form":"TREC 15-7"}', 'Fourteen-page packet and completed-signature placement QA passed; path is production locked.'),
  ('target-seller-financing', 'Seller Financing', 'Targeted Financing', 'Dedicated seller-financing form and packet QA.', 'Seller financing payload', 30, 'blocked', null, '{"financing":"seller"}', 'Production fails closed until tested.'),
  ('target-loan-assumption', 'Loan Assumption', 'Targeted Financing', 'Dedicated loan-assumption form and packet QA.', 'Loan assumption payload', 31, 'blocked', null, '{"financing":"assumption"}', 'Production fails closed until tested.'),
  ('target-paragraph4-residential', 'Paragraph 4 Residential Lease', 'Targeted Lease', 'Dedicated Paragraph 4 Residential Lease QA.', 'Paragraph 4 residential payload', 32, 'blocked', null, '{"paragraph":"4","lease":"residential"}', 'Production fails closed until supported.'),
  ('target-paragraph4-fixture', 'Paragraph 4 Fixture Lease', 'Targeted Lease', 'Dedicated Paragraph 4 Fixture Lease QA.', 'Paragraph 4 fixture payload', 33, 'blocked', null, '{"paragraph":"4","lease":"fixture"}', 'Production fails closed until supported.'),
  ('target-paragraph4-natural-resource', 'Paragraph 4 Natural Resource Lease', 'Targeted Lease', 'Dedicated Paragraph 4 Natural Resource Lease QA.', 'Paragraph 4 natural-resource payload', 34, 'blocked', null, '{"paragraph":"4","lease":"natural_resource"}', 'Production fails closed until supported.')
on conflict (scenario_key) do update set
  title = excluded.title,
  category = excluded.category,
  description = excluded.description,
  payload_name = excluded.payload_name,
  priority = excluded.priority,
  current_status = excluded.current_status,
  last_verified_release = excluded.last_verified_release,
  coverage = excluded.coverage,
  notes = excluded.notes,
  updated_at = now();

insert into public.hof_releases
  (release_key, title, environment, status, qa_status, git_branch, commit_sha, github_pr, summary, known_issues, next_action, approved_by, approved_at, deployed_at)
values
  ('trec-20-19-controlled-launch', 'TREC 20-19 controlled production launch', 'production', 'deployed', 'passed', 'main', null, 'PR #4', 'Promoted the verified buyer-offer paths behind a fail-closed production adapter.', 'Optional unverified paths remain blocked.', 'Continue targeted unlocks one path at a time.', 'Andrew Christian', now(), now()),
  ('12b-percentage-unlock', 'Paragraph 12B percentage unlock', 'production', 'deployed', 'passed', 'main', null, 'PR #6', 'Enabled verified percentage compensation paths.', null, 'Keep in golden regression coverage.', 'Andrew Christian', now(), now()),
  ('paragraph4-fail-closed-aliases', 'Paragraph 4 fail-closed aliases', 'production', 'deployed', 'passed', 'main', null, 'PR #7', 'Normalized unsupported lease aliases so incomplete packets are rejected.', null, 'Unlock each lease only after targeted QA.', 'Andrew Christian', now(), now()),
  ('buyer-temporary-lease-unlock', 'Buyer Temporary Residential Lease production unlock', 'production', 'deployed', 'passed', 'main', '25abd6cae955275a605c10af24d079b1d0f5276a', 'PR #8', 'Enabled the verified Buyer Temporary Residential Lease path.', null, 'Monitor SignWell packet assembly and retain regression coverage.', 'Andrew Christian', now(), now()),
  ('seller-temporary-lease-unlock', 'Seller Temporary Residential Lease production unlock', 'production', 'deployed', 'passed', 'main', '071b773b2be21c2ea82cb68a9c938356167c3737', null, 'Enabled the verified TREC 15-7 path after completed-signature visual QA.', null, 'Keep this path in rendered regression checks; require fresh visual QA before coordinate changes.', 'Andrew Christian', now(), now()),
  ('supabase-product-tracker-foundation', 'Supabase product and QA tracker foundation', 'production', 'in_progress', 'partial', 'agent/supabase-product-tracker', null, null, 'Live Supabase schema and seed data are complete; authenticated Admin Dashboard integration is prepared locally.', 'GitHub publication is blocked because gh is not installed in the local environment.', 'Publish the prepared branch, deploy a preview, and verify the Admin Dashboard.', 'Andrew Christian', now(), null)
on conflict (release_key) do update set
  title = excluded.title,
  environment = excluded.environment,
  status = excluded.status,
  qa_status = excluded.qa_status,
  git_branch = excluded.git_branch,
  commit_sha = excluded.commit_sha,
  github_pr = excluded.github_pr,
  summary = excluded.summary,
  known_issues = excluded.known_issues,
  next_action = excluded.next_action,
  approved_by = excluded.approved_by,
  approved_at = excluded.approved_at,
  deployed_at = excluded.deployed_at,
  updated_at = now();

insert into public.hof_qa_runs
  (scenario_id, release_name, environment, status, evidence_ref, completed_at, notes)
select id, '18B golden regression', 'staging', 'passed', 'Rendered signed PDF reviewed page-by-page', now(), 'Historical golden-packet result synchronized into the tracker on 2026-07-21.'
from public.hof_qa_scenarios
where scenario_key like 'golden-%'
on conflict (scenario_id, release_name, environment) do update set
  status = excluded.status,
  evidence_ref = excluded.evidence_ref,
  completed_at = excluded.completed_at,
  notes = excluded.notes;

insert into public.hof_qa_runs
  (scenario_id, release_name, environment, status, evidence_ref, completed_at, notes)
select id,
  case scenario_key
    when 'target-buyer-temporary-lease' then 'PR #8 production unlock'
    when 'target-seller-temporary-lease' then 'Seller temp staging'
    when 'target-12b-percentage' then 'PR #6 production unlock'
    else '18B targeted financing'
  end,
  case when scenario_key = 'target-seller-temporary-lease' then 'staging' else 'production' end,
  'passed',
  'Rendered signed PDF and field/checkbox ledger',
  now(),
  'Verified targeted path synchronized into the tracker on 2026-07-21.'
from public.hof_qa_scenarios
where scenario_key in ('target-fha', 'target-va', 'target-usda', 'target-12b-percentage', 'target-buyer-temporary-lease', 'target-seller-temporary-lease')
on conflict (scenario_id, release_name, environment) do update set
  status = excluded.status,
  evidence_ref = excluded.evidence_ref,
  completed_at = excluded.completed_at,
  notes = excluded.notes;
