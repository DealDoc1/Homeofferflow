# Brokerage setup field persistence — 2026-07-31

## Scope

The brokerage setup panel already collected account type, slug, website, and
office address fields, but the browser save payload did not persist them. This
release wires those visible fields into the existing `hof_brokerages` write.

No offer-generation route, PDF source, signer map, or legal-form workflow was
changed.

## Change

- Persist `org_type` and `slug`.
- Persist `website_url` from the actual `brandWebsiteUrl` input.
- Persist `office_address`, `office_city`, `office_state`, and `office_zip`.
- Preserve the brokerage Texas REALTORS® / NAR authorization attestation and
  fail-closed behavior.

## Verification

- Live Supabase schema contains all seven persisted identity columns plus
  `txr_all_agents_authorized`.
- OnDemand live record is active and remains fail-closed:
  `txr_all_agents_authorized = false` and no authorization timestamp.
- Focused brokerage tests: 48 passed.
- Full regression suite: 313 passed.

## Release state

- Branch: `release/intentional-prod-2026-07-31-ai-scenario-gate`
- Commit: `d82a2f7`
- Production deployment: not performed in this release step.
- Vercel Hobby deployment policy: include this in the next intentional release,
  not a routine preview deployment.
