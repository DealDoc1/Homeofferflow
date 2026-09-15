# Profile defaults without changing an active offer

Status: implemented and locally tested; not deployed or browser-verified.

## Confirmed problems and correction

- The base profile save, additional-preferences wrapper, and brokerage-default
  copy action forced saved preferences into the current interview. Saving now
  updates the profile/preferences without revising the open transaction.
  Subsequent default application still fills blank fields in matching paths.
- The additional-preferences layer reapplied financing and broker-fee choices
  on price input, even when already answered or on a different customer path.
  It now requires a signed-in matching agent/investor interview, preserves
  existing choices, and displays broker-fee fields for the current choice.
- Delayed forced defaults after account-start could overwrite a resumed draft.
  Startup default application is synchronous and non-forcing.
- The preferences wrapper previously wrote local defaults and announced
  success even when base validation failed or the save button was busy.
  It now requires a successful save for the same account, role, and profile key.
  Device-storage failure is reported separately from successful profile save.
- Profile saves retain the initiating account/role across session lookup,
  canonical-profile resolution, database lookup, and write completion. An
  obsolete response cannot replace the current account session/profile or
  continue into a write after account change. A missing refreshed session does
  not fall back to the old signed-out identity. Alias-lookup errors restore the
  button and remain errors instead of leaving a stuck save.
- Applying brokerage title defaults ignores obsolete account responses and
  restores the action button on success as well as failure. Current agreed
  title/escrow values remain unchanged.

Canonical agent-profile alias resolution and existing database owner filters
remain unchanged. Google Places, legal form sources, signing maps, recipient
delivery, and billing behavior are not altered.

## Verification

Baseline: `37578f12`.

- New runtime suite: 18 passing tests executing the actual base profile save,
  full additional-preferences wrapper, and brokerage-default action against
  DOM, local-storage, and asynchronous provider doubles.
- Counterfactual run against the baseline: 17 failed; the matching investor
  default-fill control passed. These failures directly cover overwritten offer
  terms, wrong-path preferences, false save success, obsolete account responses,
  and button recovery.
- Full Python discovery suite: 1,996 passed in 15.563 seconds.
- All 45 inline JavaScript blocks parsed successfully.
- `git diff --check`: passed.

Supabase guidance informed session/account consistency checks. Current
changelog and browser-session documentation reviewed:
https://supabase.com/changelog
https://supabase.com/docs/reference/javascript/auth-getsession
These browser checks are not a substitute for server-side authorization; no
RLS or authentication policy was weakened or changed.

## Release and remaining verification

No live database query/write, email, signature request, payment, GitHub push,
Vercel build, preview, or production deployment occurred. No new dependency,
service, database migration, or recurring cost. The existing release spending
and publication restrictions remain in force.

This is local execution evidence, not completed browser/end-to-end QA. Real
account switching, profile saves, and subsequent offer generation still need
authenticated browser verification before a production completion claim.
Record this batch as locally tested in the daily report, not deployed.
