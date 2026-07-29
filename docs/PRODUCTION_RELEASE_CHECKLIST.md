# HomeOfferFlow production release checklist

Use this checklist for every intentional HomeOfferFlow production release.
It complements, but does not replace, the source, signer, and completed-PDF
visual-QA gates required for a packet or legal-form release.

## 1. Classify the change

- [ ] List the exact changed files and affected customer workflow.
- [ ] Decide whether the batch changes a packet, legal form, PDF template,
  packet assembly, field mapping, recipient routing, or signature placement.
- [ ] If it does, stop here until a completed release-evidence file exists in
  `docs/release-evidence/`.
- [ ] If it does not, record why normal automated regression is sufficient.

## 2. Validate before publishing

- [ ] Run `git diff --check`.
- [ ] Run the full automated suite:

  ```bash
  PYTHONPATH=/private/tmp/hof_httpx_only \
  /Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest discover -s tests -p 'test_*.py'
  ```

- [ ] Run the release preflight from the exact commit intended for production:

  ```bash
  PYTHONPATH=/private/tmp/hof_httpx_only \
  /Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/release_preflight.py --base origin/main \
  --expected-deploy-author-email andrewchri@gmail.com
  ```

- [ ] For a packet/form release, add:

  ```text
  --evidence-file docs/release-evidence/<release-name>.md
  ```

- [ ] Confirm the release commit is authored by `andrewchri@gmail.com`; Vercel
  uses that author identity for the current production team.

## 3. Additional packet/form gates

- [ ] Approved source and version are recorded privately.
- [ ] Source-use authorization is explicit and recorded.
- [ ] Recipient, role, signing order, initials, signatures, and dates are
  defined.
- [ ] Every applicable blank, checkbox, initial, signature, and date was
  inspected in a rendered, completed packet.
- [ ] Existing golden packet scenarios passed and the new scenario is recorded.
- [ ] Product release authority approved the public scope.

Do not use staging coordinates or text extraction alone as evidence of PDF QA.

## 4. Production deploy

HomeOfferFlow disables automatic Git deployments to conserve Vercel Hobby
capacity. Pushes do not deploy by themselves. Bundle verified runtime work,
then run one explicit production deployment:

```bash
vercel deploy --prod --yes --scope dealdoc1s-projects
```

- [ ] Capture the deployment URL and ID.
- [ ] Wait until `vercel inspect <deployment-url> --scope dealdoc1s-projects`
  reports **Ready**.
- [ ] Confirm `https://www.homeofferflow.com/` is an alias of that deployment.

Documentation- and test-only commits do not require a separate customer-facing
Vercel deploy.

## 5. Post-deploy verification

- [ ] Check the canonical home page.
- [ ] Check each affected API route or workflow using the least-invasive test.
- [ ] Verify Stripe/Supabase/SignWell side effects only in an isolated test
  environment or an approved real transaction flow; never send Stripe test
  events into the production database.
- [ ] Confirm unchanged critical paths remain available: authentication,
  subscription/billing portal, offer dashboard, offer generation, and signing.
- [ ] Record the deployed commit, deployment URL, result, and rollback target
  in the product tracker.

## 6. Rollback decision

- [ ] If a material regression appears, identify the prior Ready production
  deployment before changing data or code.
- [ ] Roll back the alias or fix forward only after preserving the evidence.
- [ ] Do not remove legal-form evidence, subscriptions, user data, or signing
  records as part of a routine rollback.
