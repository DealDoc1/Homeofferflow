-- Reconcile tracker release references with the verified production deployment.
-- Metadata only; this does not change forms, packet generation, or signer fields.

update public.hof_roadmap_items
set
  current_release = '773732d [deploy-production] Promote verified HomeOfferFlow release',
  updated_at = now()
where slug in (
  'trec-20-19-buyer-offer',
  'buyer-temporary-lease',
  'signwell-status-tracking'
);

update public.hof_releases
set
  commit_sha = '773732de53792b031c09621e8ac275f42535bcc0',
  summary = 'Promoted the verified buyer-offer paths and current brokerage/agent runtime to production behind the verified release gate.',
  updated_at = now()
where release_key = 'trec-20-19-controlled-launch';
