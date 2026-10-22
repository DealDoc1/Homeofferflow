# Free beta partner category parity — October 22, 2026

## User outcome

Every supported partner category can use the same $0 platform-wide beta
placement, including title, lender, inspection, and surveyor. This implements
the owner's direction that all partner placements are free during beta until
further notice, on equal terms. No paid conversion is automatic.

## Implementation and validation

- `lib/beta_partner_publication.py` now recognizes all categories accepted by
  the partner platform, including title and the three other previously omitted
  supported categories.
- Title placement runtime coverage confirms a $0 fee and no signed agreement
  is falsely asserted. Existing admin authorization, qualified-lead,
  public-profile validation, privacy, and idempotency checks remain in place.
- Focused validation: 90 partner publication/admin/profile/directory tests
  passed; `git diff --check` passed.
- Full release candidate suite: `PYTHONPATH=. python -m unittest discover -s
  tests -q` — 2,925 passed, 23 skipped.
- `scripts/release_preflight.py --base origin/main
  --expected-deploy-author-email andrewchri@gmail.com` — passed.
- Vercel project `homeofferflow` showed two production deployments in the prior
  24 hours; this candidate uses one intentional production deployment. No
  routine preview was created.

## External-state boundary

This evidence file records the code release only. Kate Tucker's lead has not
yet been converted to beta or published. No database row, partner email, or
placement was changed as part of the local validation.
