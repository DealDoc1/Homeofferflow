# Complimentary partner operations — October 16, 2026

## Bounded outcome and baseline

Keep published complimentary beta partners distinct from paid partners in the
existing administrator dashboard. Production baseline: main
`6c418195898cafcae06e43e2bf4bb7621722f34b`, deployment
`dpl_2BTQMYryi7SYJbkkGRpAaGGBx9ac` on the canonical HomeOfferFlow domains.

Before this change, the actual production lifecycle function described a new
active zero-fee beta placement as “Launch period · 90 days left” and instructed
the administrator to prepare for recurring billing. The activation-rate
numerator also counted all active partner sources, including beta, while its
denominator counted paid leads.

Read-only production database verification confirmed that the Integrity First
and Darren Foster central applications both have `partner_program=beta`,
`payment_status=not_started`, and active placements with `monthly_fee=0`.
No billing correction or subscription creation is needed.

## Changed behavior

- Join the existing central application program to placement records in memory;
  do not infer beta status from a zero fee or add database reads.
- Show explicit zero-fee beta as “Complimentary beta,” without a renewal
  countdown or automatic paid conversion. Show inconsistent beta fees for
  review without changing any billing.
- Published profiles offer a profile-update email draft action, not repeated
  onboarding, checkout or agreement actions. Nothing is sent automatically.
- Limit paid activation, agreement/onboarding counts and average activation
  time to commercial paid leads. Preserve existing commercial lifecycle behavior.
- Advance the offline shell from v103 to v104 for the changed interface.

## Verification

- Focused partner Python suite: 170 tests passed, including five new tests.
- New actual-source JavaScript runtime coverage: six cases passed, invoked by
  `tests/test_partner_operations.py` via `node --test`.
- Actual admin GET-handler fixtures cover a two-beta/two-commercial cohort,
  paid conversion of 50%, exclusion from paid onboarding/agreement counts, and
  the existing 403 authorization boundary with no dataset reads.
- PWA focused suite: 69 tests passed.
- Frozen full candidate: `PYTHONPATH=. python -m unittest discover -s tests -q`
  passed 2,651 tests in 85.966 seconds, one environment-dependent skip.
  Local log: `/private/tmp/hof-partner-ops-full-20261016.log`. Diagnostic failures
  printed by negative-test fixtures are expected; the suite result is OK.
- Whitespace: `git diff --check` clean.

Fresh authenticated browser visual verification was unavailable because the Mac
was locked and browser attachment timed out. No authenticated production admin
GET or new UI screenshot is claimed. This is a text/read-model correction,
verified through actual interface logic and the real handler with fixture data.

## Release and safety boundary

The owner's standing directive authorizes normal fixes and deployment. Keep
automatic Git deployments disabled. Use one intentional existing prebuilt
production workflow only after its fresh capacity/spend guard passes. No new
paid service, preview deployment, email, invitation, billing action, permission
change or database migration is part of this batch.

Draft disclosure PR 1341 and its unapplied migration are excluded. No document
renderer, form source or signature placement is changed by this release.

After release, record the deployment identity, canonical byte comparison,
unauthenticated admin response and fresh read-only beta-terms verification.
