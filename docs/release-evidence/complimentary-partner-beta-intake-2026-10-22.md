# Complimentary partner beta intake — October 22, 2026

## User outcome

Partner applicants receive one consistent no-charge beta path across Core,
Featured, and Premier placement preferences. The application does not start
checkout, collect payment details, or convert automatically to paid service.
Review, private onboarding, written agreement, and publication checks remain
separate steps. The existing Premier workflow and completion placement and
three-profile directory cap were not changed.

## Implementation

- `api/fsbo-lead.py` marks new leads with `partner_program=beta`, returns that
  value in the existing application response, uses beta-specific receipt
  steps, and blocks partner checkout before database or Stripe access.
- `index.html` keeps the five-field application, returns after saving the beta
  lead based on the server-returned `partner_program`, prevents duplicate
  submissions after refresh, and states the same $0 terms in the homepage entry
  point, confirmation, partner admin controls, campaign invitation, and
  generated flyer. Beta placement fee controls are fixed at $0, and the intake
  no longer asks for a future paid-budget preference.
- `partners.html` and `texas-home-service-partner-guide.html` show the same
  no-charge terms, remove paid checkout timing and price claims, and retain
  application review before publication.
- The admin aggregate metric now records acknowledgement of beta terms instead
  of checkout readiness. The offline shell cache advances to v126.

## Verification

- Focused command: `PYTHONPATH=. ../txr1101-runtime/bin/python -m unittest
  tests.test_partner_checkout tests.test_partner_lead tests.test_partner_tier_ui
  tests.test_partner_landing_funnel tests.test_beta_partner_publication
  tests.test_partner_directory_impressions -q` — 111 tests passed.
- `git diff --check` passed.
- JSON-LD validation parsed all structured-data blocks in `index.html`,
  `partners.html`, and `texas-home-service-partner-guide.html`. Node parsed all
  49 inline JavaScript blocks across those pages.
- Source review covered the public landing page, partner application,
  confirmation, and admin-generated partner materials. Browser visual review
  was not completed: the ambient local URL had no listener, binding a local
  server was denied by the sandbox (`Operation not permitted`), and the browser
  refused the `file://` protocol under its security policy.

## External state and release

- No customer or partner email or invitation was sent. No database or Stripe
  write, charge, session expiration, or subscription change was performed.
- Existing hosted Stripe Checkout links and active partner subscriptions were
  not inspected. Direct links issued before the beta rule may have a separate
  lifecycle from the now-blocked application endpoint; verify that state before
  any production release or claim that all existing billing is disabled.
- No deployment or release-capacity check was performed. This is a local code
  checkpoint only; automatic Git deployment settings were not changed.
- `docs/CURRENT_PROJECT_STATE.md` is absent from this checkout. The current
  branch is `codex/purchase-disclosure-pending-guidance`, based on `d4d20ed6`
  and 11 commits ahead of `origin/main` at the time of this checkpoint. The
  production deployment revision was not independently verified.
