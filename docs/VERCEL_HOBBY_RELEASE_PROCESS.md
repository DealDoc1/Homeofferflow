# Vercel deliberate release process

## Current production cost policy (September 10, 2026)

The production team is now on Pro. The historical Hobby limits below are not
the current account's spend allowance. Keep Git deployments disabled and use
the existing production-release workflow to build on GitHub's standard Linux
runner, then upload with `--prebuilt`. Do not use a Vercel-hosted build for
routine releases. The public repository's standard GitHub-hosted runner minutes
are free; runtime traffic and other Vercel resources can still incur usage.

The workflow requires `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID`
as repository secrets, and verifies the pulled project matches the configured
production target before building. Never infer a project from a temporary
checkout directory's name.

References: [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions),
[Vercel prebuilt deployments](https://vercel.com/docs/cli/deploy#prebuilt).

## Historical limits and release checklist

For the complete cross-system gate (tests, legal-form evidence, the
confirmation-gated production deployment, and post-deploy verification), use
[`PRODUCTION_RELEASE_CHECKLIST.md`](PRODUCTION_RELEASE_CHECKLIST.md).

HomeOfferFlow disables automatic Git deployments so a branch push or merge does
not consume a Vercel deployment by itself.

The production bundle retains a conservative 12-public-function regression
guard. Internal Python adapters and private TXR renderers live under `lib/`,
not `api/`, so they are not exposed as public endpoints. The 20-19 staging
route remains in source control for controlled QA but is excluded from the
production bundle through `.vercelignore`.

The release workflow also applies a conservative 100-deployment safety
threshold per rolling 24-hour window before building. This internal protection
is separate from the public-function bundle guard above.

For each completed batch:

1. Run the full local test suite and `git diff --check`.
2. Review the intended production scope.
   - If the diff changes a packet/form PDF, packet-mapping route, or a
     dedicated form workflow, complete a release-evidence file first. Start
     from [`RELEASE_EVIDENCE_TEMPLATE.md`](RELEASE_EVIDENCE_TEMPLATE.md).
   - Run the fail-closed check before requesting deployment:

     ```bash
     python3 scripts/release_preflight.py \
       --base origin/main \
       --evidence-file docs/release-evidence/<release-name>.md
     ```

   - This check requires approved source, authorization, signing plan,
     rendered signed-PDF QA, regression evidence, and release authority. It does
     not replace any of those human gates.
   - Vercel also evaluates the **author email on the commit being deployed**.
     The release commit must use an email that belongs to the HomeOfferFlow
     Vercel team. For the current deployment team, add this author check to the
     same command:

     ```bash
     python3 scripts/release_preflight.py \
       --base origin/main \
       --expected-deploy-author-email andrewchri@gmail.com
     ```

     This does not grant anyone product authority. It only prevents Vercel from
     silently blocking a valid build because its commit author lacks Vercel-team
     access.
3. Merge the verified pull request.
4. Run `.github/workflows/production-release.yml` from the exact checked-out
   production commit. Enter `DEPLOY` explicitly; the workflow performs the
   prebuilt Vercel deployment, readiness check, and canonical-domain check.
5. Verify `https://www.homeofferflow.com/` and the affected workflow.

The repository also retains the read-only manual GitHub Actions **release gate**
(`.github/workflows/release-gate.yml`) for verification-only runs. The
confirmation-gated `production-release.yml` workflow is the only approved path
that deploys to Vercel.

This keeps the release cadence deliberate and avoids separate automatic preview
and production builds. It does not relax the legal-form source, signer-plan, or
completed-PDF visual-QA gates.
