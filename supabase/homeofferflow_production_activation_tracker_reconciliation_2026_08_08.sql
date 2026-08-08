-- Reconcile the production release record with the verified live runtime.
-- This is tracker data only; it does not alter packet generation, RLS, or
-- customer data.

begin;

update public.hof_releases
set commit_sha = '0c66ef3',
    vercel_deployment_url = 'https://homeofferflow-58avpsqgn-dealdoc1s-projects.vercel.app',
    summary = 'Verified production runtime for TREC 20-19 purchase packets, supported addenda, temporary leases, and SignWell routing. Field, checkbox, signature-line, golden-render, and live smoke QA recorded in docs/release-evidence/production-activation-field-checkbox-signature-qa-2026-08-08.md.',
    known_issues = 'TXR-1501, TXR-1506, TXR-1507, TXR-1508, executable listing agreements, seller disclosures, and lease-listing workflows remain fail-closed pending authenticated brokerage-member preview, signer-plan review, and completed signed-PDF visual QA.',
    next_action = 'Run the next authenticated brokerage-member preview and completed-signature QA for one gated workflow before enabling it.',
    updated_at = now()
where release_key = 'trec-20-19-controlled-launch'
  and environment = 'production';

commit;

-- Verification:
-- select release_key, commit_sha, vercel_deployment_url, summary, known_issues,
--        next_action, updated_at
-- from public.hof_releases
-- where release_key = 'trec-20-19-controlled-launch';
