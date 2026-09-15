# Profile and IABS loading isolation

Status: locally implemented and tested; not deployed or browser-verified.

## Customer outcome

- The base and canonical-profile loaders apply only the latest applicable
  request for the same account and role. A successful intervening profile save
  takes precedence over an older read.
- Account identity changes clear cached profile/IABS presentation and deselect
  the optional IABS attachment. No saved PDF, remote record, or local offer
  draft is deleted. Token refresh for the same account preserves current work.
- A session-change counter prevents responses from an earlier sign-in from
  being applied after signing back into the same account. Profile saves and
  brokerage-default copying use the same boundary.
- IABS loading ignores obsolete results and errors. An older response cannot
  replace a newer document or resurrect a locally removed document reference.
  The profile/IABS wrapper stops obsolete follow-up loads and rendering.
- Canonical linked-email profile resolution remains in place; its owner query
  was exercised as a positive control. No brokerage seat or approval added.

## Verification

Baseline: `0004fa2d`.

- New profile-loading runtime suite: 23 passing cases executing the actual
  loaders, session-cache reset wiring, and IABS wrapper with deferred query
  promises. Against the baseline, 20 failed and three positive controls passed.
- Two additional existing-save regression cases cover signing back into the
  same account while profile/default saves are pending.
- Combined profile-loading/default-safety suites: 43 passed.
- Final full suite: 1,997 passed in 15.566 seconds.
- All 45 inline JavaScript blocks parse; `git diff --check` passes.

Supabase guidance informed the account/role/session checks. Current auth-event
documentation and changelog were reviewed:
https://supabase.com/docs/reference/javascript/auth-onauthstatechange
https://supabase.com/changelog
Browser guards do not replace server-side authorization. Existing ownership
filters, alias permissions, RLS, and storage access policies are unchanged.

## Release limits

These are local runtime tests, not authenticated browser or live-database QA.
No customer records, PDFs, messages, signatures, payments, or external settings
were changed. No GitHub publication, Vercel build/preview/deployment, new
dependency, or recurring service cost. Existing spending/publication limits
remain in effect. Record as locally tested in the daily report, not deployed.
