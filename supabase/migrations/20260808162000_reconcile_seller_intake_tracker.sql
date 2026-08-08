-- Reconcile the roadmap tracker with the seller-intake integrity release.
-- This records the production foundation only; seller legal-form execution
-- remains source- and completed-signature-QA gated.

begin;

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = '26f4e2a seller-lead intake integrity (2026-08-08)',
  known_issues = 'Agent-private seller leads and listing workspaces are live with constrained intake, explicit authenticated owner policies, and aggregate-only brokerage reporting. Seller disclosure, listing agreement, and lease-listing execution remain source-gated.',
  next_action = 'Run authenticated one- and two-seller TREC-55-1/TREC-61-0 previews, then complete signer mapping and completed-signature visual QA before enabling seller disclosure sending.',
  updated_at = now()
where slug in ('seller-workflow', 'fsbo-workflow');

commit;
