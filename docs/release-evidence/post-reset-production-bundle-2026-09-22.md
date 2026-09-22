# Post-reset coordinated production bundle — September 22, 2026

## Release boundary

- Prior verified production revision: `133a32bff9a736544c8bf9c9d04cd549c11b8570`.
- Exact application candidate revision: `c1678c818c98b61cc11253d7e2b387b85b921f68`. The release commit may be the later protected-main merge containing this evidence-only reconciliation; the production tree remains the attached manifest.
- Candidate manifest: 142 deployable files / 21,239,246 bytes.
- Canonical production origin: `https://www.homeofferflow.com`.
- Deployment method: one intentional, prebuilt Vercel production deployment. Automatic Git deployments and routine previews remain disabled.
- Customer scope: the accumulated HomeOfferFlow reliability, plain-language interview, agent activation, PWA return, signing recovery, purchase-packet, and Texas-form corrections merged since the prior production revision.

This record authorizes one coordinated corrective release. It does not convert a local or historical QA result into a production result. Each post-release status must be recorded separately after the exact deployed revision and canonical runtime are verified.

## Database-first release sequence

The candidate code depends on six production capability migrations that were confirmed absent on September 21, 2026. A seventh migration installs the service-only readiness contract that verifies the complete set. Apply and verify them in this order immediately before the code deployment:

1. `20260915103000_canonical_agent_profile_aliases.sql`
2. `20260915185113_durable_checkout_email_delivery.sql`
3. `20260915193756_server_owned_packet_usage.sql`
4. `20260915203004_protect_offer_packet_autosave.sql`
5. `20260915233303_private_buyer_checkout_payloads.sql`
6. `20260915234223_expired_checkout_payload_cleanup.sql`
7. `20260921203652_homeofferflow_release_schema_readiness.sql`

The database and application changes are one release unit. Do not apply the behavior-changing migrations hours in advance, and do not deploy the candidate code while the required tables, functions, trigger, and `hof_usage_events.generation_key` column are absent. The release workflow calls the service-only `hof_release_schema_readiness` contract after it pulls the production environment and before it spends Vercel build or deployment capacity; a missing capability, credential, or unreadable response stops the release. Also verify migration history and the named schema objects before starting the Vercel build.

The September 21 live read-only preflight confirmed all seven migrations are absent, all 20 referenced production columns have the expected types, both canonical-profile seed identities exist, the canonical agent profile exists, no release trigger name conflicts exist, and the subscription user key is unique. All 44 existing usage rows had a user, offer, and valid billing month; there were no duplicate subscription users. This proves dependency readiness only—the migrations remain intentionally unapplied until the coordinated release.

Rollback is application-first: move the production alias back to the prior Ready deployment if a material regression appears. Preserve the additive tables, immutable receipts, usage records, and customer data; do not drop them during routine rollback.

## Packet and form scope

The release comparison includes the production offer / purchase offer renderer and TREC 20-19 purchase contract, plus the following Texas REALTORS® source-specific renderers:

- TXR-1501 Residential Buyer/Tenant Representation Agreement — Long Form
- TXR-1506 General Information and Notice to Consumers
- TXR-1507 Residential Buyer/Tenant Representation Agreement — Short Form
- TXR-1508 Unrepresented Customer Showing Form
- TXR-1905 Addendum for Reservation of Oil, Gas, and Other Minerals
- TXR-1914 Seller Financing Addendum
- TXR-1917 Environmental Assessment, Threatened or Endangered Species, and Wetlands Addendum
- TXR-1919 Addendum for Property Subject to Mandatory Membership in a Property Owners Association
- TXR-1948 Addendum Concerning Right to Terminate Due to Lender's Appraisal
- TXR-1953 Addendum Regarding Residential Leases
- TXR-1954 Addendum Regarding Fixture Leases

The purchase packet also adds or corrects seller financing, loan assumption, environmental assessment, mineral reservation, hydrostatic testing, Paragraph 4 lease elections, backup-contract, appraisal, HOA, sale-contingency, lead-disclosure, repair, non-realty, and contract-term continuations. No brokerage seat is required to use the public-agent interview. Google address completion remains in place.

The changed shared renderer named `txr_addenda_layout` is the TXR addenda layout used by those listed source-specific addenda; it is not an unidentified additional form.

## Approved source and authorization

- Approved source: the existing production TREC 20-19 asset and the exact private TXR source revisions already fingerprinted in the source vault and catalog evidence.
- Authorization: Andrew Christian, HomeOfferFlow product owner and counsel, supplied the source files and has repeatedly authorized their use and release for all agents without a brokerage-seat gate.
- Source revision evidence: `txr-source-inventory-2026-07-31.md`, `txr-source-vault-sync-2026-08-07.md`, `txr-source-imprint-2026-09-18.md`, and `addenda-source-imprint-2026-09-18.md`.
- Agent attestation: the existing point-of-use form-use attestation remains the only agent acknowledgement. This release adds no broker approval, source-owner intake, or new customer gate.

## Signing plan

- Signing plan: recipient roles, parallel invitations, per-form page offsets, and source-relative field geometry remain server-owned and covered by the signing-map tests.
- Signing order remains disabled for the applicable buyer/seller and relationship-form workflows; recipients can sign in parallel.
- Existing SignWell documents and historical signed customer PDFs remain immutable. Do not replace, cancel, resend, or cite an old packet as proof of the corrected production revision.
- The compact provider packet used only the approved test recipients and disabled reminders. No duplicate provider request is needed for the six forms already closed by that evidence.

## Rendered signed-PDF QA and completed signature visual QA

Completed signature visual QA and local rendered-PDF QA are deliberately separated below.

Authenticated QA was performed through the signed-in HomeOfferFlow and SignWell workspaces for the provider documents referenced below. Local synthetic renders are identified separately and are not described as authenticated provider completion evidence.

| Scope | Evidence before deployment | Post-release requirement |
| --- | --- | --- |
| TXR-1501, TXR-1507, TXR-1905, TXR-1914, TXR-1917, TXR-1919 | `compact-signwell-geometry-qa-2026-09-18.md`: completed 14-page SignWell packet, all 54 fields visually inspected, full suite green | Do not resend; verify canonical renderer identity and signing-map revision only |
| TXR-1506 | `txr-1506-single-signer-signed-pdf-qa-2026-09-07.md` and `txr-1506-provider-signature-prefix-repair-2026-09-09.md` | Run only the still-missing signer/conditional cases; keep status partial until completed |
| TXR-1508 | `txr-1508-completed-packet-review-2026-09-11.md` records the provider placement failure; corrected source-map rendering and regression are complete | Create one compact corrected one-customer and genuine two-customer QA packet after release; inspect before marking verified |
| TXR-1948 | `txr-1948-private-review-release-2026-08-24.md`, `txr-1948-signature-rule-calibration-2026-09-09.md`, `purchase-appraisal-candidate-2026-09-18.md`, and `txr-addenda-execution-clearance-2026-09-18.md` | Verify the corrected canonical-field output in a completed provider packet before marking the new answer matrix provider-verified |
| TXR-1953 and TXR-1954 | `txr-1953-1954-signing-release-2026-09-08.md` and `lease-addendum-completed-pdf-alignment-2026-09-15.md` record completed-provider evidence and the defects it exposed; corrected local renders pass | Verify fresh corrected completed PDFs after release; keep status partial until those checks pass |
| TREC 20-19 and supported purchase addenda | `bundled-packet-golden-baseline-2026-09-21.md`, `paragraph4-natural-resource-lease-2026-09-21.md`, and the source-specific packet evidence referenced below | Verify both Paragraph 4C choices and the read-only production packet runtime; create no customer packet for smoke testing |

The release is corrective: where the completed provider PDF exposed a defect, the candidate fixes the known placement rather than preserving the known-bad production geometry. The roadmap must continue to say `partial`, `failed`, or `pending provider verification` for the explicitly listed remaining matrices until fresh corrected PDFs are inspected.

## Regression evidence

- Candidate regression: 2,381 repository tests passed locally on September 21, 2026.
- Pull requests #1253 and #1254 passed protected checks. Protected-main runs `35667003856` and `35668079386` passed after merge; their intentional Vercel release jobs were skipped.
- `bundled-packet-golden-baseline-2026-09-21.md` records the reviewed 20-page packet and regenerated privacy-safe golden manifest.
- `compact-signwell-geometry-qa-2026-09-18.md` records the completed six-form provider packet and refreshed privacy-safe geometry baselines.
- `signing-reliability-main-merge-2026-09-18.md`, `stable-packet-delivery-retries-2026-09-15.md`, `purchase-offer-delivery-recovery-2026-09-15.md`, and `durable-signature-recovery-2026-09-15.md` cover concurrent invitations and delivery recovery.
- `ondemand-mobile-enrollment-2026-09-21.md` records the aggregate trial-funnel evidence, mobile-first enrollment ordering, autofill-safe intent measurement, and the unchanged price/billing boundary.
- `ondemand-sign-in-clarity-2026-09-21.md` records the truthful secure-link action label and privacy-safe direct/referral attribution without storing a referrer URL or identity.
- `ondemand-enrollment-resilience-2026-09-21.md` records the nonblocking brokerage-configuration load and the unchanged server-side eligibility and checkout authority.
- `form-library-session-recovery-2026-09-21.md` records one-time expired-session recovery and suppression of repeat rejected-token function calls.
- `ondemand-install-handoff-2026-09-21.md` records the single post-checkout PWA install surface, privacy-safe accept/dismiss measurement, and unchanged vendor-cost boundary.
- `ondemand-magic-link-resilience-2026-09-21.md` records recovery from a rejected passwordless-auth request so a prospective subscriber is never stranded on a disabled enrollment button.
- `ondemand-consent-preservation-2026-09-21.md` records same-account token-refresh behavior that preserves the agent's visible terms choice while still resetting consent when identities change.
- `ondemand-session-bootstrap-2026-09-21.md` records startup recovery that keeps the auth listener active when the saved-session read fails.
- `seller-financing-purchase-packet-2026-09-18.md`, `loan-assumption-packet-foundation-2026-09-18.md`, `environmental-purchase-packet-2026-09-18.md`, `mineral-purchase-packet-2026-09-18.md`, and `hydrostatic-purchase-packet-2026-09-15.md` cover the new packet paths.
- The exact release commit must rerun the full suite, golden packet rendering, standalone geometry, Supabase branch preflight, release preflight, and whitespace check in GitHub Actions.

## Release authority

- Release authority: Andrew Christian, HomeOfferFlow product owner and counsel.
- Approval basis: standing instruction to deploy the discussed roadmap enhancements and necessary fixes without requesting repeated approval, while avoiding unnecessary Vercel overage.
- Authorized scope: one coordinated production release after the September 22 billing reset and only after fresh Vercel credit headroom is confirmed.
- This authority does not permit fabricated QA, duplicate customer sends, deletion of signing evidence, or a second Vercel deployment merely to correct an avoidable release-process error.

## Production verification and acceptance

The release is ready to enter the production workflow only after all of these preconditions are true:

1. Vercel's new billing cycle is visible and retains at least the configured $3 infrastructure-credit reserve.
2. The exact candidate is authored by `andrewchri@gmail.com` and protected-main CI is green.
3. The seven ordered migrations are applied; the six capability migrations and service-only readiness contract report every required table, function, trigger, RLS setting, and column ready.
4. The release preflight passes against the prior production revision using this evidence file.

After deployment:

- confirm the deployment is Ready and both canonical domains alias it;
- run the read-only production PWA and packet-runtime checks;
- verify agent sign-in continuation, saved-agent installed-app return, the OnDemand phone-sized enrollment fold, customer-friendly packet recovery, Paragraph 4C choices, checkout recovery, and signing status on the canonical site;
- scan runtime logs for new errors;
- update every affected roadmap item using exact production evidence; and
- run only the narrowly scoped provider QA packets still identified above.

Do not mark the release production-verified merely because the build completed.
