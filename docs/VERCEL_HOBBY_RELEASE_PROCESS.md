# Vercel Hobby release process

HomeOfferFlow disables automatic Git deployments so a branch push or merge does
not consume a Vercel deployment by itself.

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
3. Merge the verified pull request.
4. From the checked-out production commit, run one explicit production deploy:

   ```bash
   vercel deploy --prod --yes
   ```

5. Verify `https://www.homeofferflow.com/` and the affected workflow.

This keeps the release cadence deliberate and avoids separate automatic preview
and production builds. It does not relax the legal-form source, signer-plan, or
completed-PDF visual-QA gates.
