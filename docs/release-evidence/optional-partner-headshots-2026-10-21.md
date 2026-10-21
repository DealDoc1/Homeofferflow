# Optional partner headshots - October 21, 2026

## Bounded user outcome and release authority

The owner suggested a headshot in the top-right of partner banners. This
independent slice starts from production main 24d619eb, not customer listing
draft PR 1353. It extends central partner creative and existing placements:
public directory, inspection banner, insurance-planning banner and offer
follow-up. The owner's standing implementation/SQL/push/merge/deploy directive
covers this change. No partner invitation, charge, agreement, subscription or
message is sent. No new partner is published and no person's photo is inferred.

## Implementation

- One nullable explicitly public headshot URL on the existing central lead.
  Private account avatars/contact data are never fallbacks. Public output
  retains only opted-in creative for active platform placements.
- Existing expiring, partner-scoped signed-image upload path; PNG/JPEG/WebP,
  2 MB, same bucket and no new Storage permission. Photo omission preserves
  the current image; explicit removal clears it. A forged other-partner path
  fails before saving or agreement dispatch.
- One shared safe portrait renderer, accessible alternative text, fixed image
  dimensions, lazy loading and no-referrer requests. Failed images hide their
  slot; no supplied photo retains the original banner markup/layout.
- Mobile top-right placement retains readable company logos and full-width
  descriptions/actions. Desktop placements reserve only necessary photo space.
  Setup includes an optional native file picker and an accessible removal
  control; field help remains readable and the checkbox does not stretch.
- Reset stale file selections when another setup record opens. Existing
  website/call links, provider choice, aggregate analytics and beta terms stay
  unchanged. No customer information is automatically shared.
- PWA shell v114 and the small public profile stylesheet; no private API or
  document response is added to offline caching. Future apps can use the same
  public API field rather than reimplement partner data.

## Tests and browser evidence

Focused partner/lifecycle/source-readiness/PWA run: 152 Python tests pass.
The wrappers execute the real JavaScript renderer/upload/submit handlers,
including optional/removal/no-logo, input escaping, invalid URL/type/size,
request shape, upload failure recovery and unchanged routing/tracking.
These overlapping checks are not summed with earlier runs.

Real isolated PostgreSQL: 21 assertions pass, no TCP/cloud/provider access.
The actual migration preserves grants/RLS, leaves existing rows null, accepts
valid secure URLs, rejects malformed values and supports explicit removal.

Local browser fixture: actual component source and actual validated onboarding/
public-profile functions, with fictional rows/storage adapter and no external
writes. It uses the public HomeOfferFlow icon as clearly labeled test artwork,
not as an approved partner headshot. Desktop 1280px and 390px phone directory
were visually reviewed. Inspection/insurance and follow-up phone layouts and
desktop insurance were inspected; no horizontal overflow. Missing-photo
fallback has no portrait placeholder. Phone setup removal saved through the
real onboarding function and the resulting directory response removed only
that fictional partner's image. A fixture HTTP logo was correctly rejected by
the unchanged HTTPS rule; the fixture was corrected rather than weakening it.
Browser review caught and corrected mobile reserved space, full-width checkbox
styling and help contrast. Screenshots remain outside Git in
`../partner-headshots-2026-10-21/`; no real partner/customer data is in them.

This is not authenticated production onboarding/upload proof. The unchanged
production Storage boundary is covered by focused contract/ownership tests;
no fresh partner link, agreement or public photo is created solely for smoke QA.

## Coordinated backwards-compatible schema

The pinned CLI 2.81.3 generated a migration at 20261021200504. The hosted tool
applied identical SQL and assigned authoritative version 20261021202420;
the local file is renamed to that version without changing SQL bytes. The
SQL uses a 5-second lock timeout and only a nullable column/validated format
constraint. No backfill, activation, grant or RLS change. The release checker
adds a zero-row column probe before deploying the matching application code.

Hosted verification: table grants unchanged
`{postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres}`, RLS true, one
existing policy, nullable YES, format constraint validated. Zero public
headshots are populated. Customer v2, purchase v1 and rental-source v1 readiness
all remain ready with no missing capabilities. Security advisors retain the
same two existing categories (16 findings each); none concerns this lead
table. The Supabase skills guided least privilege and bounded locks; existing
GraphQL/RLS findings were not used as a reason to break unrelated account access.

## Release boundary

Full frozen regression and exact-head CI follow focused/visual checks. Keep
automatic Git deployments disabled and use the existing intentional prebuilt
production workflow with its single built-in target/spend check. Do not bundle
unfinished sale/lease customer migrations or SignWell acceptance work. No
provider map, legal document or signature geometry changes in this release.

Rollback is the previous immutable application deployment. The nullable column
can remain safely installed; do not delete partner creative or remove grants
as a rollback shortcut. After deployment, verify canonical profile assets and
public API, existing partner routing/labels and unchanged no-photo placements.
Do not claim measured lead, revenue or conversion improvement from this UI work.
