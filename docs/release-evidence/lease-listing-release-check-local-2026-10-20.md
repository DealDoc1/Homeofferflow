# Lease-listing coordinated release check — October 20, 2026

Status: implemented and tested locally; **not deployed or run against hosted
production**. Follows package-composition checkpoint `b9a278ed`. The intended
user outcome is to release the listing code only with its required database
capabilities present, without weakening any customer workflow or account access.
Scope is `scripts/check_production_schema_readiness.py` and its focused tests.
Documented production baseline is `bfd03d99` / shell v112. No Vercel usage poll
or preview deployment was made.

The existing production workflow already calls the schema checker before its
intentional release. The checker now also calls the existing service-only
`hof_lease_listing_schema_readiness()` RPC and requires its exact
`homeofferflow-lease-listing-schema-v1` contract. Wrong/malformed contracts,
nonboolean readiness, missing or invalid failure lists, reported missing lease
capabilities, and HTTP failures cannot be treated as success. Even `ready=true`
with a nonempty missing list fails. The sale-listing v3 and purchase-disclosure
checks remain required; the lease result does not replace them.

This uses the already committed, **unapplied** additive migration
`20261020231654_add_txr1102_lease_listing_drafts.sql`; no SQL, grants, RLS,
authentication, source access or external settings were changed. The RPC only
checks catalog capabilities. Existing REST column probes use `limit=0` and do
not read application rows or contacts. Modern API keys remain API-key headers,
not bearer tokens; credentials are not printed.

Verification:

```sh
../txr1101-runtime/bin/python -m unittest \
  tests.test_production_schema_readiness \
  tests.test_standalone_form_schema_contract -q
```

**19 tests pass, exit 0; `git diff --check` passes.** Isolated HTTP fixtures cover
the successful seven-request path, lease constraint/baseline failures, HTTP
401/403/404/503, malformed payloads, incompatible contracts, preserved purchase
failure propagation, modern/legacy authentication headers and safe output.
Static migration-contract assertions preserve the private invoker-only wrapper.
The unchanged migration's real isolated PostgreSQL proof remains the 36
assertions recorded in `txr1102-private-api-local-2026-10-20.md`; it was not
rerun for this client-script-only change. Hosted schema readiness is not inferred
from these fixtures, and cannot pass until the coordinated migration is applied.

The Supabase skill prompted review of current official function privileges/docs
and changelog before implementation. No SDK, TLS configuration, extension,
provider, dependency or migration change was required. Automatic Git deployments
remain disabled. No messages, invitations, billing changes or hosted writes.

Still required for the complete lease-listing release: actual rental flood and
lease lead source adapters and their private intake support, changed provider
rendering QA, final exact-head regression/CI, coordinated migrations and one
intentional production release with canonical checks. This checkpoint is not a
claim that the live site already has the new lease workflow.
The subsequent source-registration checkpoint resolves TXR-1102 registration
and source-login access; both related official PDFs are now available locally.
