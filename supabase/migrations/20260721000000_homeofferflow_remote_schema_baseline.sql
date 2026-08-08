-- Baseline schema pulled from the live HomeOfferFlow project via Supabase catalog metadata.
-- Schema-only: no production rows, auth users, tokens, or storage objects are included.
-- This baseline exists so ordered migrations can replay on an isolated branch.
create extension if not exists pgcrypto;
create schema if not exists private;

create table if not exists public."audit_log" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "transaction_id" uuid,
  "offer_id" uuid,
  "actor_user_id" uuid,
  "actor_email" text,
  "action" text not null,
  "metadata" jsonb default '{}'::jsonb not null,
  primary key ("id")
);

create table if not exists public."documents" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "offer_id" uuid not null,
  "doc_type" text not null,
  "file_url" text not null,
  primary key ("id")
);

create table if not exists public."help_requests" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "transaction_id" uuid,
  "offer_id" uuid,
  "requester_email" text not null,
  "requester_name" text,
  "type" text not null,
  "status" text default 'new'::text not null,
  "notes" text,
  primary key ("id")
);

create table if not exists public."hof_agent_documents" (
  "id" uuid default gen_random_uuid() not null,
  "user_id" uuid not null,
  "document_type" text not null check (document_type = 'iabs'::text),
  "storage_bucket" text default 'agent-documents'::text not null check (storage_bucket = 'agent-documents'::text),
  "storage_path" text not null,
  "original_filename" text not null,
  "mime_type" text default 'application/pdf'::text not null check (mime_type = 'application/pdf'::text),
  "byte_size" bigint not null check (byte_size > 0 AND byte_size <= 10485760),
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_agent_profiles" (
  "user_id" uuid not null,
  "agent_name" text,
  "license_number" text,
  "agent_email" text,
  "agent_phone" text,
  "brokerage_name" text,
  "brokerage_license" text,
  "preferred_title_company" text,
  "preferred_escrow_agent" text,
  "preferred_escrow_address" text,
  "default_option_fee" numeric default 250,
  "default_option_days" integer default 7,
  "default_earnest_amount" numeric,
  "default_title_payer" text default 'seller'::text,
  "default_survey_choice" text default 'sellerExisting'::text,
  "default_survey_if_rejected_paid_by" text default 'seller'::text,
  "created_at" timestamptz default now(),
  "updated_at" timestamptz default now(),
  primary key ("user_id")
);

create table if not exists public."hof_ai_offer_review_rate_limits" (
  "rate_key" text not null check (rate_key ~ '^[a-f0-9]{64}$'::text),
  "window_start" timestamptz not null,
  "request_count" integer default 0 not null check (request_count >= 0),
  "updated_at" timestamptz default now() not null,
  primary key ("rate_key", "window_start")
);

create table if not exists public."hof_ai_offer_reviews" (
  "id" uuid default gen_random_uuid() not null,
  "user_id" uuid,
  "offer_id" uuid,
  "score" integer,
  "summary" text,
  "risks" jsonb,
  "suggestions" jsonb,
  "created_at" timestamptz default now(),
  primary key ("id")
);

create table if not exists public."hof_brokerage_form_sources" (
  "id" uuid default gen_random_uuid() not null,
  "brokerage_id" uuid not null,
  "form_code" text not null check (form_code = ANY (ARRAY['TXR-1501'::text, 'TXR-1506'::text, 'TXR-1507'::text, 'TXR-1508'::text, 'TXR-1101'::text, 'TXR-1102'::text, 'TXR-1406'::text, 'TXR-1418'::text, 'TREC-55-1'::text, 'TREC-61-0'::text])),
  "source_revision" text not null,
  "status" text default 'draft'::text not null check (status = ANY (ARRAY['draft'::text, 'approved'::text, 'retired'::text])),
  "storage_bucket" text default 'brokerage-form-sources'::text not null check (storage_bucket = 'brokerage-form-sources'::text),
  "storage_path" text not null,
  "original_filename" text not null,
  "mime_type" text default 'application/pdf'::text not null check (mime_type = 'application/pdf'::text),
  "byte_size" bigint not null check (byte_size > 0 AND byte_size <= 10485760),
  "authorization_attested" boolean default false not null,
  "authorized_by_user_id" uuid,
  "authorized_at" timestamptz,
  "notes" text,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  "source_sha256" text check (source_sha256 IS NULL OR source_sha256 ~ '^[0-9a-f]{64}$'::text),
  primary key ("id")
);

create table if not exists public."hof_brokerage_invites" (
  "id" uuid default gen_random_uuid() not null,
  "brokerage_id" uuid not null,
  "email" text not null,
  "role" text default 'agent'::text not null check (role = 'agent'::text),
  "status" text default 'pending'::text not null check (status = ANY (ARRAY['pending'::text, 'accepted'::text, 'expired'::text, 'revoked'::text])),
  "invite_token" text default encode(extensions.gen_random_bytes(16), 'hex'::text) not null,
  "invited_by" uuid,
  "accepted_by" uuid,
  "accepted_at" timestamptz,
  "created_at" timestamptz default now(),
  "expires_at" timestamptz default (now() + '14 days'::interval) not null,
  primary key ("id")
);

create table if not exists public."hof_brokerage_members" (
  "id" uuid default gen_random_uuid() not null,
  "brokerage_id" uuid not null,
  "user_id" uuid not null,
  "email" text,
  "role" text default 'agent'::text check (role = ANY (ARRAY['agent'::text, 'broker_admin'::text, 'owner'::text])),
  "status" text default 'active'::text check (status = ANY (ARRAY['pending'::text, 'active'::text, 'suspended'::text, 'removed'::text])),
  "invited_by" uuid,
  "created_at" timestamptz default now(),
  "updated_at" timestamptz default now(),
  "txr_agent_authorized" boolean default false not null,
  "txr_agent_attested_by" uuid,
  "txr_agent_attested_at" timestamptz,
  "suspension_reason" text check (suspension_reason IS NULL OR (suspension_reason = ANY (ARRAY['billing'::text, 'manual'::text]))),
  primary key ("id")
);

create table if not exists public."hof_brokerages" (
  "id" uuid default gen_random_uuid() not null,
  "name" text not null,
  "dba_name" text,
  "license_number" text,
  "logo_url" text,
  "brand_color" text default '#2563eb'::text,
  "website_url" text,
  "contact_name" text,
  "contact_email" text,
  "contact_phone" text,
  "disclaimer" text,
  "default_title_company" text,
  "default_title_contact" text,
  "default_title_email" text,
  "default_title_phone" text,
  "created_by" uuid,
  "created_at" timestamptz default now(),
  "updated_at" timestamptz default now(),
  "org_type" text default 'brokerage'::text,
  "slug" text,
  "office_address" text,
  "office_city" text,
  "office_state" text default 'TX'::text,
  "office_zip" text,
  "user_cap" integer default 5,
  "billing_status" text default 'trial'::text,
  "plan_name" text default 'Brokerage Trial'::text,
  "is_active" boolean default true,
  "txr_all_agents_authorized" boolean default false not null,
  "txr_authorization_attested_by" uuid,
  "txr_authorization_attested_at" timestamptz,
  primary key ("id")
);

create table if not exists public."hof_feedback" (
  "id" uuid default gen_random_uuid() not null,
  "user_id" uuid,
  "role" text,
  "email" text,
  "issue_type" text,
  "message" text,
  "page_url" text,
  "user_agent" text,
  "status" text default 'new'::text,
  "created_at" timestamptz default now(),
  "calibration_scenario" text,
  primary key ("id")
);

create table if not exists public."hof_investor_profiles" (
  "user_id" uuid not null,
  "investor_entity_name" text,
  "signer_name" text,
  "signer_title" text,
  "investor_email" text,
  "investor_phone" text,
  "mailing_address" text,
  "preferred_title_company" text,
  "preferred_escrow_agent" text,
  "preferred_escrow_address" text,
  "default_offer_type" text,
  "default_option_fee" numeric default 250,
  "default_option_days" integer default 7,
  "default_earnest_amount" numeric,
  "created_at" timestamptz default now(),
  "updated_at" timestamptz default now(),
  primary key ("user_id")
);

create table if not exists public."hof_listing_workspaces" (
  "id" uuid default gen_random_uuid() not null,
  "brokerage_id" uuid not null,
  "agent_user_id" uuid not null,
  "seller_lead_id" uuid,
  "listing_kind" text not null check (listing_kind = ANY (ARRAY['sale'::text, 'lease'::text])),
  "property_address" text not null check (length(TRIM(BOTH FROM property_address)) >= 3 AND length(TRIM(BOTH FROM property_address)) <= 400),
  "seller_names" text[] not null check (cardinality(seller_names) >= 1 AND cardinality(seller_names) <= 4),
  "status" text default 'intake'::text not null check (status = ANY (ARRAY['intake'::text, 'source_pending'::text, 'draft'::text, 'ready_for_review'::text, 'archived'::text])),
  "requested_workflows" jsonb default '[]'::jsonb not null check (jsonb_typeof(requested_workflows) = 'array'::text),
  "confidential_notes" text,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_offer_events" (
  "id" uuid default gen_random_uuid() not null,
  "offer_id" uuid,
  "user_id" uuid,
  "event_type" text not null,
  "status" text,
  "message" text,
  "metadata" jsonb default '{}'::jsonb not null,
  "created_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_offer_signing_parties" (
  "id" uuid default gen_random_uuid() not null,
  "offer_id" uuid not null,
  "created_by_user_id" uuid not null,
  "party_side" text not null check (party_side = ANY (ARRAY['buyer'::text, 'seller'::text])),
  "party_index" smallint not null check (party_index >= 1 AND party_index <= 4),
  "full_name" text not null check (length(TRIM(BOTH FROM full_name)) >= 1 AND length(TRIM(BOTH FROM full_name)) <= 250),
  "email" text,
  "phone" text,
  "mailing_address" text,
  "signing_role" text default 'party'::text not null check (signing_role = ANY (ARRAY['party'::text, 'buyer'::text, 'seller'::text, 'landlord'::text, 'tenant'::text])),
  "signing_required" boolean default false not null,
  "execution_status" text default 'draft'::text not null check (execution_status = ANY (ARRAY['draft'::text, 'pending'::text, 'signed'::text, 'declined'::text, 'voided'::text])),
  "signwell_recipient_id" text,
  "signed_at" timestamptz,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_offers" (
  "id" uuid default gen_random_uuid() not null,
  "user_id" uuid,
  "role" text check (role IS NULL OR (role = ANY (ARRAY['homebuyer'::text, 'agent'::text, 'investor'::text, 'brokerage_admin'::text, 'admin'::text]))),
  "buyer_name" text,
  "buyer_email" text,
  "property_address" text,
  "offer_price" numeric,
  "status" text default 'draft'::text check (status IS NULL OR (status = ANY (ARRAY['Draft'::text, 'Generated'::text, 'Sent'::text, 'Sent for Signature'::text, 'Awaiting Signature'::text, 'Awaiting Buyer Signature'::text, 'Buyer Viewed'::text, 'Partially Signed'::text, 'Partially Buyer Signed'::text, 'Signed'::text, 'Buyer Signed'::text, 'Buyer Signatures Complete'::text, 'Submitted'::text, 'Accepted'::text, 'Rejected'::text, 'Deleted'::text, 'Expired'::text]))),
  "payload" jsonb,
  "created_at" timestamptz default now(),
  "updated_at" timestamptz default now(),
  "offer_data" jsonb default '{}'::jsonb,
  "last_updated" timestamptz default now(),
  "deleted_at" timestamptz,
  "buyer_phone" text,
  "buyer2_name" text,
  "buyer2_email" text,
  "seller_name" text,
  "agent_name" text,
  "agent_email" text,
  "agent_phone" text,
  "agent_license" text,
  "agent_brokerage" text,
  "agent_broker_license" text,
  "financing_type" text,
  "closing_date" date,
  "title_company" text,
  "signwell_document_id" text,
  "generated_at" timestamptz,
  "property_city" text,
  "property_state" text,
  "property_zip" text,
  "property_county" text,
  "loan_amount" numeric,
  "down_payment" numeric,
  "earnest_money" numeric,
  "option_fee" numeric,
  "option_days" integer,
  "escrow_agent" text,
  "signwell_status" text,
  primary key ("id")
);

create table if not exists public."hof_partner_leads" (
  "id" uuid default gen_random_uuid() not null,
  "partner_type" text default 'other'::text not null check (partner_type = ANY (ARRAY['title'::text, 'lender'::text, 'inspection'::text, 'surveyor'::text, 'home_warranty'::text, 'insurance'::text, 'roofing'::text, 'hvac'::text, 'plumbing'::text, 'electrical'::text, 'foundation_structural'::text, 'general_contractor'::text, 'pest_termite'::text, 'septic_well'::text, 'restoration'::text, 'photography_video'::text, 'staging'::text, 'repairs_handyman'::text, 'cleaning'::text, 'moving_storage'::text, 'lawn_pool'::text, 'security_smart_home'::text, 'other'::text])),
  "company_name" text not null,
  "contact_name" text not null,
  "contact_email" text not null,
  "contact_phone" text,
  "website_url" text,
  "market_area" text not null,
  "customer_focus" text,
  "monthly_budget_range" text default 'discuss'::text not null check (monthly_budget_range = ANY (ARRAY['under_250'::text, '250_499'::text, '500_999'::text, '1000_plus'::text, 'discuss'::text])),
  "preferred_model" text default 'founding_pilot'::text not null check (preferred_model = ANY (ARRAY['founding_pilot'::text, 'monthly_placement'::text, 'market_exclusive'::text, 'discuss'::text])),
  "message" text,
  "source" text default 'website_partner_modal'::text not null,
  "utm_source" text,
  "utm_medium" text,
  "utm_campaign" text,
  "utm_content" text,
  "landing_page" text,
  "status" text default 'new'::text not null check (status = ANY (ARRAY['new'::text, 'contacted'::text, 'qualified'::text, 'waitlist'::text, 'converted'::text, 'declined'::text])),
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  "payment_status" text default 'not_started'::text not null check (payment_status = ANY (ARRAY['not_started'::text, 'checkout_started'::text, 'paid'::text, 'failed'::text, 'refunded'::text])),
  "onboarding_status" text default 'not_started'::text not null check (onboarding_status = ANY (ARRAY['not_started'::text, 'ready'::text, 'in_progress'::text, 'complete'::text])),
  "stripe_checkout_session_id" text,
  "stripe_payment_intent_id" text,
  "stripe_customer_id" text,
  "stripe_subscription_id" text,
  "subscription_status" text,
  "current_period_end" timestamptz,
  "paid_at" timestamptz,
  primary key ("id")
);

create table if not exists public."hof_partner_placements" (
  "id" uuid default gen_random_uuid() not null,
  "brokerage_id" uuid,
  "partner_type" text not null,
  "partner_name" text not null,
  "contact_name" text,
  "contact_email" text,
  "contact_phone" text,
  "website_url" text,
  "logo_url" text,
  "market_area" text,
  "placement_tier" text default 'founding'::text,
  "monthly_fee" numeric,
  "is_active" boolean default true,
  "created_at" timestamptz default now(),
  "source_lead_id" uuid,
  "agreement_confirmed_at" timestamptz,
  "activated_at" timestamptz,
  primary key ("id")
);

create table if not exists public."hof_platform_admins" (
  "user_id" uuid not null,
  "label" text,
  "created_at" timestamptz default now() not null,
  primary key ("user_id")
);

create table if not exists public."hof_profiles" (
  "id" uuid not null,
  "email" text,
  "role" text default 'agent'::text check (role = ANY (ARRAY['agent'::text, 'investor'::text, 'brokerage_admin'::text])),
  "created_at" timestamptz default now(),
  "updated_at" timestamptz default now(),
  "brokerage_id" uuid,
  "team_name" text,
  "is_brokerage_admin" boolean default false,
  primary key ("id")
);

create table if not exists public."hof_qa_results" (
  "id" uuid default gen_random_uuid() not null,
  "run_id" uuid not null,
  "page_number" integer check (page_number IS NULL OR page_number > 0),
  "section" text,
  "field_name" text not null,
  "expected" text,
  "actual" text,
  "status" text default 'not_tested'::text not null check (status = ANY (ARRAY['pass'::text, 'fail'::text, 'watch'::text, 'not_tested'::text, 'not_applicable'::text])),
  "coordinate_locked" boolean default false not null,
  "proposed_change" text,
  "reviewer_notes" text,
  "created_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_qa_runs" (
  "id" uuid default gen_random_uuid() not null,
  "scenario_id" uuid not null,
  "release_id" uuid,
  "release_name" text not null,
  "environment" text default 'staging'::text not null check (environment = ANY (ARRAY['local'::text, 'staging'::text, 'production'::text])),
  "status" text default 'queued'::text not null check (status = ANY (ARRAY['queued'::text, 'running'::text, 'passed'::text, 'failed'::text, 'blocked'::text])),
  "packet_name" text,
  "evidence_ref" text,
  "git_commit" text,
  "github_pr" text,
  "executed_by" uuid,
  "started_at" timestamptz,
  "completed_at" timestamptz,
  "notes" text,
  "created_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_qa_scenarios" (
  "id" uuid default gen_random_uuid() not null,
  "scenario_key" text not null unique,
  "title" text not null,
  "category" text not null,
  "description" text,
  "payload_name" text,
  "expected_pages" integer check (expected_pages IS NULL OR expected_pages > 0),
  "priority" integer default 999 not null,
  "active" boolean default true not null,
  "current_status" text default 'not_tested'::text not null check (current_status = ANY (ARRAY['not_tested'::text, 'partial'::text, 'passed'::text, 'failed'::text, 'blocked'::text, 'staging_passed'::text, 'production'::text])),
  "last_verified_release" text,
  "last_verified_at" timestamptz,
  "coverage" jsonb default '{}'::jsonb not null,
  "notes" text,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_releases" (
  "id" uuid default gen_random_uuid() not null,
  "release_key" text not null unique,
  "title" text not null,
  "environment" text default 'staging'::text not null check (environment = ANY (ARRAY['local'::text, 'staging'::text, 'production'::text])),
  "status" text default 'planned'::text not null check (status = ANY (ARRAY['planned'::text, 'in_progress'::text, 'qa'::text, 'staging_passed'::text, 'deployed'::text, 'rolled_back'::text, 'blocked'::text])),
  "qa_status" text default 'not_tested'::text not null check (qa_status = ANY (ARRAY['not_tested'::text, 'partial'::text, 'passed'::text, 'failed'::text, 'blocked'::text])),
  "git_branch" text,
  "commit_sha" text,
  "github_pr" text,
  "vercel_deployment_url" text,
  "summary" text,
  "known_issues" text,
  "next_action" text,
  "approved_by" text,
  "approved_at" timestamptz,
  "deployed_at" timestamptz,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_roadmap_items" (
  "id" uuid default gen_random_uuid() not null,
  "category" text not null,
  "title" text not null,
  "description" text,
  "priority" integer default 999,
  "status" text default 'planned'::text,
  "created_at" timestamptz default now(),
  "slug" text,
  "environment" text default 'backlog'::text not null,
  "qa_status" text default 'not_tested'::text not null,
  "target_release" text,
  "current_release" text,
  "known_issues" text,
  "next_action" text,
  "github_ref" text,
  "requested_by" text default 'Andrew Christian'::text not null,
  "is_locked" boolean default false not null,
  "metadata" jsonb default '{}'::jsonb not null,
  "updated_at" timestamptz default now() not null,
  "completed_at" timestamptz,
  primary key ("id")
);

create table if not exists public."hof_seller_disclosure_drafts" (
  "id" uuid default gen_random_uuid() not null,
  "brokerage_id" uuid not null,
  "agent_user_id" uuid not null,
  "listing_workspace_id" uuid,
  "disclosure_source_id" uuid not null,
  "water_source_id" uuid,
  "disclosure_source_revision" text not null,
  "water_source_revision" text,
  "status" text default 'draft'::text not null check (status = ANY (ARRAY['draft'::text, 'ready_for_review'::text, 'void'::text])),
  "property_address" text not null check (length(btrim(property_address)) >= 3 AND length(btrim(property_address)) <= 400),
  "seller_names" jsonb not null check (jsonb_typeof(seller_names) = 'array'::text AND jsonb_array_length(seller_names) >= 1 AND jsonb_array_length(seller_names) <= 2),
  "buyer_names" jsonb default '[]'::jsonb not null check (jsonb_typeof(buyer_names) = 'array'::text AND jsonb_array_length(buyer_names) >= 0 AND jsonb_array_length(buyer_names) <= 2),
  "response_data" jsonb default '{}'::jsonb not null check (jsonb_typeof(response_data) = 'object'::text),
  "water_rights_data" jsonb default '{}'::jsonb not null check (jsonb_typeof(water_rights_data) = 'object'::text),
  "seller_review_attested" boolean default false not null,
  "seller_review_attested_at" timestamptz,
  "seller_review_attested_by" uuid,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_seller_disclosure_review_links" (
  "id" uuid default gen_random_uuid() not null,
  "draft_id" uuid not null,
  "brokerage_id" uuid not null,
  "agent_user_id" uuid not null,
  "seller_email" text not null check (length(btrim(seller_email)) >= 3 AND length(btrim(seller_email)) <= 254),
  "token_hash" text not null unique,
  "verification_code_hash" text not null,
  "expires_at" timestamptz not null,
  "revoked_at" timestamptz,
  "viewed_at" timestamptz,
  "verified_at" timestamptz,
  "session_token_hash" text unique,
  "session_expires_at" timestamptz,
  "seller_attested_at" timestamptz,
  "seller_attested_name" text,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  "seller_name" text check (seller_name IS NULL OR length(btrim(seller_name)) >= 1 AND length(btrim(seller_name)) <= 180),
  "seller_index" smallint check (seller_index IS NULL OR seller_index >= 1 AND seller_index <= 2),
  primary key ("id")
);

create table if not exists public."hof_seller_leads" (
  "id" uuid default gen_random_uuid() not null,
  "user_id" uuid,
  "brokerage_id" uuid,
  "seller_type" text default 'fsbo'::text,
  "property_address" text,
  "seller_name" text,
  "seller_email" text,
  "seller_phone" text,
  "asking_price" numeric,
  "mortgage_balance" numeric,
  "desired_close_date" date,
  "notes" text,
  "status" text default 'new'::text,
  "created_at" timestamptz default now(),
  "updated_at" timestamptz default now(),
  primary key ("id")
);

create table if not exists public."hof_standalone_agreements" (
  "id" uuid default gen_random_uuid() not null,
  "brokerage_id" uuid not null,
  "agent_user_id" uuid not null,
  "form_source_id" uuid not null,
  "form_code" text not null check (form_code = ANY (ARRAY['TXR-1501'::text, 'TXR-1506'::text, 'TXR-1507'::text, 'TXR-1508'::text])),
  "source_revision" text not null,
  "status" text default 'draft'::text not null check (status = ANY (ARRAY['draft'::text, 'ready_for_review'::text, 'sent'::text, 'signed'::text, 'void'::text, 'failed'::text])),
  "client_names" jsonb not null check (jsonb_typeof(client_names) = 'array'::text AND jsonb_array_length(client_names) >= 1 AND jsonb_array_length(client_names) <= 2),
  "agreement_data" jsonb default '{}'::jsonb not null check (jsonb_typeof(agreement_data) = 'object'::text),
  "signwell_document_id" text unique,
  "signwell_status" text,
  "generated_storage_bucket" text,
  "generated_storage_path" text,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  "sent_at" timestamptz,
  "signed_at" timestamptz,
  primary key ("id")
);

create table if not exists public."hof_stripe_webhook_events" (
  "id" uuid default gen_random_uuid() not null,
  "stripe_event_id" text not null unique,
  "event_type" text not null,
  "livemode" boolean not null,
  "stripe_subscription_id" text,
  "stripe_customer_id" text,
  "processing_state" text default 'received'::text not null check (processing_state = ANY (ARRAY['received'::text, 'processed'::text, 'ignored'::text, 'failed'::text])),
  "error_code" text,
  "received_at" timestamptz default now() not null,
  "processed_at" timestamptz,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."hof_subscriptions" (
  "id" uuid default gen_random_uuid() not null,
  "user_id" uuid not null,
  "role" text default 'agent'::text not null,
  "plan" text default 'agent_starter'::text not null,
  "status" text default 'beta'::text not null check (status = ANY (ARRAY['beta'::text, 'trialing'::text, 'active'::text, 'past_due'::text, 'canceled'::text, 'free_admin'::text])),
  "stripe_customer_id" text,
  "stripe_subscription_id" text,
  "stripe_price_id" text,
  "current_period_start" timestamptz,
  "current_period_end" timestamptz,
  "packet_limit" integer default 10 not null,
  "beta_expires_at" timestamptz,
  "created_at" timestamptz default now() not null,
  "updated_at" timestamptz default now() not null,
  "cancel_at_period_end" boolean default false,
  "cancel_at" timestamptz,
  "brokerage_id" uuid,
  "launch_source" text,
  "trial_started_at" timestamptz,
  "trial_ends_at" timestamptz,
  primary key ("id")
);

create table if not exists public."hof_usage_events" (
  "id" uuid default gen_random_uuid() not null,
  "user_id" uuid not null,
  "offer_id" uuid,
  "event_type" text not null,
  "quantity" integer default 1 not null,
  "billing_month" text not null,
  "metadata" jsonb default '{}'::jsonb not null,
  "created_at" timestamptz default now() not null,
  primary key ("id")
);

create table if not exists public."offer_intakes" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "listing_link" text,
  "address_line1" text,
  "city" text,
  "state" text,
  "zip_code" numeric,
  "year_built" numeric,
  "has_hoa" boolean default false,
  "offer_price" numeric,
  "earnest_money" numeric,
  "option_fee" numeric,
  "option_days" numeric,
  "closing_date" date,
  "non_realty_items" text,
  "financing_type" text,
  "status" text default 'draft'::text,
  primary key ("id")
);

create table if not exists public."offer_invites" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "offer_id" uuid not null,
  "invited_email" text not null,
  "invited_name" text,
  "token" text not null unique,
  "expires_at" timestamptz,
  "first_viewed_at" timestamptz,
  primary key ("id")
);

create table if not exists public."offer_terms" (
  "offer_id" uuid not null,
  "updated_at" timestamptz default now() not null,
  "terms" jsonb default '{}'::jsonb not null,
  primary key ("offer_id")
);

create table if not exists public."offers" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "transaction_id" uuid not null,
  "created_by" uuid,
  "version_number" integer not null,
  "status" text default 'draft'::text not null,
  "summary" text,
  primary key ("id")
);

create table if not exists public."parties" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "transaction_id" uuid not null,
  "role" text not null,
  "full_name" text,
  "email" text not null,
  "phone" text,
  "user_id" uuid,
  "is_initiator" boolean default false not null,
  primary key ("id")
);

create table if not exists public."payments" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "transaction_id" uuid,
  "offer_id" uuid,
  "user_id" uuid,
  "provider" text not null,
  "provider_payment_id" text,
  "purpose" text not null,
  "amount_cents" integer not null,
  "currency" text default 'USD'::text not null,
  "status" text default 'created'::text not null,
  primary key ("id")
);

create table if not exists public."sign_requests" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "offer_id" uuid not null,
  "provider" text not null,
  "provider_request_id" text,
  "status" text default 'created'::text not null,
  primary key ("id")
);

create table if not exists public."transactions" (
  "id" uuid default gen_random_uuid() not null,
  "created_at" timestamptz default now() not null,
  "created_by" uuid,
  "state" text default 'TX'::text not null,
  "address_line1" text not null,
  "address_line2" text,
  "city" text not null,
  "region" text not null,
  "postal_code" text not null,
  "source_url" text,
  "source_domain" text,
  "import_status" text default 'none'::text not null,
  "import_confidence" integer default 0 not null,
  "status" text default 'draft'::text not null,
  primary key ("id")
);

