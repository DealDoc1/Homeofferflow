# Vercel Hobby release process

HomeOfferFlow disables automatic Git deployments so a branch push or merge does
not consume a Vercel deployment by itself.

For each completed batch:

1. Run the full local test suite and `git diff --check`.
2. Review the intended production scope.
3. Merge the verified pull request.
4. From the checked-out production commit, run one explicit production deploy:

   ```bash
   vercel deploy --prod --yes
   ```

5. Verify `https://www.homeofferflow.com/` and the affected workflow.

This keeps the release cadence deliberate and avoids separate automatic preview
and production builds. It does not relax the legal-form source, signer-plan, or
completed-PDF visual-QA gates.
