# Reliable brokerage setup saves — October 16, 2026

## Bounded batch

Outcome: a delayed brokerage setup/default save must remain associated with
its initiating account and brokerage, and setup must not claim success when
the account connection failed. Scope: two existing index.html save handlers,
the branding save button, offline-shell version and focused runtime tests.
Baseline: production d8d2f1ae9fed3612594b4285690c65bb5132357c /
dpl_BMWKohegQPEsznmKhtSCS4vgSZ2F on the canonical HomeOfferFlow domains.
Keep automatic Git deployment disabled. Allow only one intentional existing
prebuilt production workflow after fresh spend/capacity checks. Required
evidence: actual-source delayed-response tests, broader regression, independent
CI and canonical post-release identity/runtime checks.

## Reproduction and correction

The original actual-source runtime fixture failed ten of eleven initial
cases. A delayed shared-default response replaced the new account's BB
brokerage with the previous BA record, and its stale failure overwrote the
new account's status. Branding fallback could start another write after the
account changed. A profile-link failure displayed success, and repeated taps
started two branding writes. These are controlled fictional fixtures, not
claims of observed customer data loss or a completed live broker-admin pass.

- Capture the starting account ID, account epoch and brokerage ID; ignore
  obsolete responses and failures. Stop before follow-up/fallback writes if
  the context changed. Pin compatibility fallback to the original brokerage.
- Disable the branding save button during the operation; restore both save
  buttons after completion/failure. Repeated branding taps start one write.
- Request the existing profile update's id/brokerage_id readback and require
  that exact connection before reporting success. Empty or denied responses
  are errors. Keep a newly saved brokerage in the same account for a retry
  when only linking failed, so retry updates it instead of inserting again.
- Use a concise success message without inferring new administrative access.
- Advance production offline shell from v104 to v105. No form rendering,
  document generation, signing or paid behavior changes.

## Verification

- Thirteen actual-source JavaScript cases pass, including ordinary update,
  compatibility fallback, create/retry, duplicate tap, account switch,
  same-user sign-out epoch, brokerage switch, stale failure, failed link and
  an empty link response. Python wrapper runs this matrix in the normal suite.
- Ninety-four focused integration checks pass: brokerage saves/load isolation,
  branding propagation, shared source foundation, license defaults and PWA.
- Full regression: 2,652 tests in 86.202 seconds, OK with one environment skip;
  local log /private/tmp/hof-brokerage-save-full-20261016.log. The new final
  success message was shortened during the run; the actual-source save matrix
  was rechecked afterward and passed. No logic changed after the run began.
- Patch whitespace is clean. A stalled initial negative fixture was stopped
  and corrected to resolve unexpected writes; no customer process was stopped.
- Read-only production policy query confirms hof_profiles SELECT and UPDATE
  remain restricted to auth.uid() = id, including UPDATE WITH CHECK. Existing
  server broker context independently requires active owner/broker_admin
  membership. No RLS, grants, membership, profile flag payload or API privilege
  was expanded. Supabase's current update documentation confirms explicit
  select readback; no SDK/dependency change was needed.

Fresh authenticated visual admin QA is not claimed: the last browser inventory
showed a locked Mac. Real customer/brokerage records were not changed for QA.
These interface/response fixes are verified by controlled actual-source
execution; full brokerage-wide onboarding QA remains tracked separately.

## Release boundary

The owner's standing authorization covers normal corrections and deployment.
Use the existing normal PR/CI/merge/release process. No outbound message,
invitation, test packet, subscription, charge, credential export, schema change
or preview deployment is needed. Draft disclosure PR 1341 is excluded and must
reserve a shell version newer than v105 before its own eventual release.

Production identity, smoke and observability evidence will be recorded after
the single release; no documentation-only follow-up deployment is requested.
