# Production release revalidation - September 18, 2026

Read-only external verification at approximately **21:25 UTC / 4:25 PM
America/Chicago**. These are dated observations, not a release approval or a
claim that the working branch is production-ready.

## Production identity

Vercel's authenticated deployment list and deployment-detail API report:

- Project: `homeofferflow`, `prj_LupoeEEcWigvtw6CII2bL46l0RB3`.
- Deployment: `dpl_G9HSsdVzDXCMbm2GamFbEWWZ2CUW`, `READY`, production.
- Aliases include both `homeofferflow.com` and `www.homeofferflow.com`.
- Created: September 15, 2026, 15:45:43 UTC / 10:45 AM America/Chicago.
- Reported Git revision: `133a32bff9a736544c8bf9c9d04cd549c11b8570`.
- Reported commit: merge PR #1226, signing-recipient retry.
- Deployment source: CLI. Git metadata identifies the reported source revision;
  it does not independently prove an uploaded tree was free of local edits.
- [Vercel deployment record](https://vercel.com/dealdoc1s-projects/homeofferflow/G9HSsdVzDXCMbm2GamFbEWWZ2CUW).

The checked local branch at `9d49c8ed` is **92 commits** beyond that reported
revision, with 338 changed files. This count includes tests and evidence, not
92 separate customer features. Those commits have not been deployed by this
work. Do not treat a local fix, local commit, or GitHub main alone as live proof.

Source inspection at the reported production revision still shows TXR-1507's
first client signature y=714 and date y=720, x=720, width=48. The local candidate
uses y=684 and date y=692, x=696, width=72. This aligns with the supplied signed
client document's observed placement defect; it does not replace a live
post-release completed-document check.

## Current cost boundary - freshly verified

Read the authenticated [Vercel Usage dashboard](https://vercel.com/dealdoc1s-projects/~/usage),
Current Billing Cycle, All Products, All Projects:

| Dashboard item | Observed value |
| --- | --- |
| Billing cycle | August 22 to September 22, 2026 |
| Included usage credit | $20.00 of $20.00 consumed |
| On-demand charges | $1.39 |
| Infrastructure subtotal | $21.39 |
| Build CPU charge | $21.24 |
| Build CPU usage | 109 hours |
| Subscription license | $20.00 |
| Credits applied | -$20.00 |
| Displayed total | $21.39 |

The build detail attributes 104h56m (96.3%) to `homeofferflow`, 1h56m to
`homeofferflow-release`, and 1h52m to `homeofferflow-main`, with small amounts
on other/deleted projects. Normal function/network usage is not the main
cost shown. The UI says data may be up to one hour old; these values can change.

**The old Hobby-plan quota is not today's explanation.** The account displays
Pro, and the relevant current constraint is exhausted usage credit with existing
overage. Do not initiate a build under the owner's no-overage instruction.
Recheck the account after the September 22 reset rather than assuming the
reset itself proves available headroom. Do not pause the production site or
change billing/spend settings as a substitute for authorization.

The local production workflow already builds on the CI runner and deploys a
prebuilt artifact. Preserve that approach, disabled automatic Git deployments,
local verification, and one coordinated release rather than routine previews.
The existing 100-deployments-per-day safety check measures frequency only;
it is **not a spending or remaining-credit check**.

## Pending database dependencies - freshly verified

Authenticated Supabase inspection of production project `acqylchftrjjoablvqyq`
used migration history and a SELECT-only catalog query. No customer rows were
read. The five local migrations below are absent from the returned history:

| Local migration | Purpose and observed production gap |
| --- | --- |
| `20260915185113_durable_checkout_email_delivery.sql` | Email receipt/outbox table and preservation function/trigger absent |
| `20260915193756_server_owned_packet_usage.sql` | Packet-generation table, usage generation-key column and four packet functions absent |
| `20260915203004_protect_offer_packet_autosave.sql` | Offer draft-protection function/trigger absent |
| `20260915233303_private_buyer_checkout_payloads.sql` | Private checkout-payload table and preservation function/trigger absent |
| `20260915234223_expired_checkout_payload_cleanup.sql` | Depends on the absent checkout-payload table |

Catalog results independently confirm all three tables and the usage column
are absent, and none of the seven named functions or three triggers are
present. This avoids assuming migration-history absence alone proves schema
absence. These gaps concern the **unreleased code**, not a claim that all
currently deployed checkout or email operations are broken.

Do not deploy the entire local batch before these dependencies are applied and
verified in the coordinated release. In particular, the packet-usage migration
explicitly requires the corresponding server integration/browser-write
retirement; offer draft protection also needs compatibility verification against
the release. Do not apply those behavior-changing migrations in isolation while
the code deployment is held. Check actual grants, RLS, triggers, conditional
writes and advisors as part of that release, not only migration filenames.

## Signing QA and next release work

The latest local regression is 2,252 tests: 2,250 pass, and two approved-map
reference comparisons still fail. Their baselines have not been regenerated
to hide the unverified changes. See [runtime asset evidence](pdf-runtime-assets-2026-09-18.md).

The completed nonbinding TXR-1507 one-client/associate specimen has measured
provider evidence. That does not establish second-client/broker combinations,
new answer continuations, or every other changed form. Keep the exact existing
[provider-evidence scope](txr1507-client-placement-candidate-2026-09-18.md).

Next work is to finish the remaining form/provider coverage, reconcile the
approved references only against actual evidence, verify the five migrations
and code as one release, and revalidate spending capacity before the single
intentional deployment. Production verification must follow that deployment.
Do not represent the 92-commit batch as deployed or release-ready today.

## Actions not taken

No build, preview, deployment, public push, migration, customer-record mutation,
email, signing request, reminder, paid resource or billing-setting change was
performed. The one temporary Chrome usage tab was closed after inspection;
existing user tabs were left alone. No source or signed customer PDF was
uploaded or modified. The roadmap goal remains active; cost and remaining
verification constrain the release, not all local development.
