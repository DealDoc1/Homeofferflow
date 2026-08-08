# Billing and seller-QA hardening release evidence — 2026-08-08

## Scope

This batch contains subscription-suspension guardrails, brokerage-admin
membership protections, live tracker reconciliation, and private seller
disclosure QA tooling. It does not change the TREC-20-19 packet renderer,
buyer offer generation, legal-form source mappings, signer coordinates, or
SignWell send behavior.

## Verified checkpoint

- Repository: `DealDoc1/Homeofferflow`
- Main release commit: `f3dc77fc3e0d74fc4510b0e69b45e31357730505`
- Source branch commit before merge: `de73faf977b5f477012a34f09e772d64fcd8a9a3`
- Pull request: #156
- Full automated suite: 477 tests passed.
- Golden rendered-packet regression: approved baseline matched, including the
  seller-temporary-lease scenario.
- `git diff --check`: passed.
- Release preflight against `origin/main`: passed; no packet/form source or
  mapping change detected.
- GitHub PR workflow run: `31230546546`, successful.

## Seller QA safety boundary

The seller QA bundle creates only private unsigned previews for approved
TREC-55-1 and TREC-61-0 sources. It records one- and two-seller metadata and
explicitly rejects signing side effects. Authenticated point-of-use QA,
recipient mapping, completed-signature visual QA, and release authorization
remain required before seller disclosure signing is enabled.

## Deployment boundary

- Vercel Git deployments remain disabled under the Hobby-cap policy.
- No Vercel deployment was triggered by this batch.
- Production remains on the prior intentional release until the confirmation-
  gated production workflow is run with `DEPLOY` for this exact commit.
- After deployment, verify the canonical domain, billing lifecycle behavior,
  brokerage access scoping, and unchanged offer-generation/signing paths.
