# OnDemand checkout-return activation recovery

## Scope

- Outcome: an agent returning from checkout can recover late sign-in and delayed access confirmation without repeating checkout or seeing another account's stale result.
- Baseline production `256b5f4825860d516d116c4adac1674fd5e282f3`, READY deployment `dpl_FHFpH89QWFbBuv9LsGkJjMHxxpTY`; scoped page `ondemand.html`, actual-source runtime coverage and synchronized PWA v93. One guarded prebuilt release; no routine preview.
- Existing server GET `create-subscription-checkout?launch=ondemand&status=access` still requires verified identity, active membership and current subscription. No API, database schema, billing terms, roles, credentials or contract/signature changes.
- Read-only database audit confirmed Tyler is an active OnDemand broker_admin; both owner login addresses are active agents, with firm license 9010832. This is not authenticated broker-admin browser QA or a full brokerage launch pass.

## Reproduction and fix

- Seven initial actual-source runtime cases reproduced five failures: late auth never rechecked activation; delayed saved-session data overwrote a newer identity; late access responses updated signed-out/other-account controls; delayed activation had no user retry.
- Identity epoch invalidates stale access responses. One shared in-flight access check prevents token refresh from duplicating checks. The current auth event wins over a delayed initial saved-session read. Same-account token refresh preserves the existing acknowledgment.
- Late authentication resumes server-authoritative access confirmation. Workspace/start/install controls only show after that account receives access=true, never merely because the URL contains checkout=success.
- A separate Check my workspace access button retries read-only confirmation. Checkout-return screens hide repeat enrollment/checkout controls; standard enrollment retains the unchanged legal acknowledgment and 60-day/$29 terms. A recovered sign-in clears its obsolete startup warning.

## Verification boundary

- Eight actual-source runtime cases pass, including pending response, recovered sign-in, obsolete identity, token refresh, sign-out, account switch, delayed-access retry and ordinary enrollment versus return controls. Focused OnDemand Python set: 86 tests pass.
- Local browser fixture serves the real launch HTML with fictional auth and mocked local API responses only. No external invitation, payment, membership change, legal acknowledgment or customer-record write. Actual browser saw the retry state while access=false; late sign-in then access=true showed the ready workspace. Runtime tests exercised the retry click itself.
- Desktop and 390x844 phone ready-state layout visually reviewed. Screenshot `/private/tmp/hof-ondemand-activation-ready-mobile.png`; temporary viewport reset. The local fixture is not evidence that live Stripe checkout or an actual new agent activation was completed.
- Full frozen candidate, independent CI, guarded release, canonical page and deployment error scan are recorded after completion. The remaining branding/admin/invitation and actual new-agent checkout matrix stays partial.
- Full local candidate ran 2,551 tests in 84.822 seconds: one historical source assertion expected unverified success-URL-based controls. Updated it to require checkout return plus confirmed ready access, without modifying the runtime candidate. Focused funnel checks re-run; independent protected CI/release regression remains required.
