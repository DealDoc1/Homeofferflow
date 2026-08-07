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
  PYTHONPATH=/private/tmp/homeofferflow_test_deps:/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python \
  /Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest discover -s tests -p 'test_*.py'
  ```

- [ ] Run the release preflight from the exact commit intended for production:

  ```bash
  PYTHONPATH=/private/tmp/homeofferflow_test_deps:/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python \
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
- [ ] Confirm the exact Vercel project and `main` commit that will be deployed;
  do not invoke an unverified or stale deploy-hook URL.

## 2A. Account, billing, and brokerage-admin regression

For any release that changes authentication, subscriptions, brokerage access,
or dashboard authorization:

- [ ] Verify platform-admin fallback access using the focused admin regression
  suite; a missing browser subscription row must not block platform admins.
- [ ] Verify brokerage administrators and agents do not receive the platform
  admin fallback or any free-access bypass.
- [ ] Verify real active, canceled, and trial subscription rows remain
  authoritative.
- [ ] Verify the OnDemand launch path still requires a card, shows the 60-day
  trial and $29/month renewal, and preserves the normal billing path.
- [ ] Verify brokerage-admin roster, invitation, branding, shared-defaults,
  and restricted-form readiness surfaces remain scoped to the administrator's
  own brokerage.
- [ ] Verify the canonical site and the least-invasive authenticated dashboard
  check after deployment.

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

## 3A. Restricted Texas REALTORS® source gate

For any release that touches a restricted Texas REALTORS® / NAR workflow:

- [ ] Brokerage authorization is recorded by the brokerage administrator; it
  is not inferred from a license number.
- [ ] Each agent attests individually at the point of use.
- [ ] If a source PDF is private to a brokerage, it was uploaded through the
  platform source-owner intake by an authorized platform administrator or
  source owner, with the printed revision and exact SHA-256 fingerprint.
- [ ] The source record is private and brokerage-scoped.
- [ ] Source approval has not been mistaken for workflow activation; no draft,
  signer fields, email, or SignWell document is created by source intake alone.
- [ ] Signer plan, rendered completed packet QA, completed-signature visual QA,
  and release-authority approval are recorded separately before activation.

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
- [ ] Scan production runtime errors for the prior 24 hours before and after
  the deployment; investigate any new 5xx or function errors before release
  sign-off.
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
