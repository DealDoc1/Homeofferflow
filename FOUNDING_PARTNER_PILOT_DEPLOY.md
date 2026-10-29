# Partner Beta Placements — Operations and Release

This runbook describes the current complimentary partner beta. The older paid
90-day pilot terms and sponsored workflow-card proposal have been retired.
Do not use those rates, checkout steps, or placement promises.

## Current placement rules

- Every partner tier is complimentary during beta, with no payment or automatic
  paid conversion.
- The public directory lists at most three profiles per category: the active
  Premier first, followed by up to two other partners.
- Only the single top active Premier across HomeOfferFlow appears in guided
  transaction workflows and the offer-completion confirmation.
- Other Premier profiles, Featured Partners, and Founding Partners remain in the
  directory only.
- Sponsored placements are labeled. HomeOfferFlow never preselects a provider;
  users may choose any provider or none.
- The shared partner API owns directory and workflow selection through its
  `surface=directory` and `surface=workflow` views. Keep these business rules
  server-side so future clients can reuse them.
- An approved profile remains private until its secure setup, profile, and
  written-agreement review are complete.

## Release checks

Before release, run the focused partner API, directory, intake, completion, and
public-profile checks. Review the partner page and beta application at desktop
and phone widths. Run the complete test suite once for the release candidate.
Keep automatic Git deployments disabled. Do not create routine previews.
Before one intentional prebuilt production deployment, verify the exact
candidate, release checks, current Vercel headroom, and operating costs. Then
verify the canonical production host and deployed commit.

Do not submit a real partner application or send a partner communication for
routine QA. Use fictional local fixtures. No payment or customer packet is
needed to verify partner placement visibility.

## Current evidence

The shared placement selector and completion rendering are implemented and
covered by [partner visibility evidence](docs/release-evidence/partner-premier-visibility-2026-10-22.md).
The public copy is aligned and locally reviewed in
[placement copy evidence](docs/release-evidence/partner-placement-copy-alignment-2026-10-22.md).
These local changes are not proof of deployment or production behavior.
