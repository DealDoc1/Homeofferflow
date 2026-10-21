# Returning-browser partner script compatibility - October 21, 2026

Production baseline: e5354770, PR 1356, shell v114. Its exact-head CI and
intentional production run 39671634933 passed, including 2,921 tests (24 source
opt-in skips), schema/target/build/canonical/PWA/API checks. Deployment:
dpl_GY8xwgUSyNiTVZQw7HbmjUpTGBzJ. Canonical fresh HTTP checks matched all four
partner JS/CSS files to the reviewed tree and verified both public profiles,
zero published headshots, no private fields and unchanged Integrity routing.

## Actual browser failure and bounded repair

The already-open production browser had loaded the preceding public helper
before this release. On ordinary reload it received the new directory markup
but showed the provider-retry fallback. The categorized production API still
returned HTTP 200 with the correct active profile. Asset responses retain the
existing `public, max-age=900, s-maxage=86400, stale-while-revalidate=604800`
policy; a new page can therefore coexist with a browser-cached old helper that
has no portrait method. This returning-browser failure was not caught by fresh
HTTP comparisons or synthetic full tests. No full browser success is claimed
for the first release.

The actual-source directory regression now reproduces the old interface plus
strict new method call and confirms the retry fallback. The corrected renderer
with that same old interface preserves the provider name and call action.
Matching compatibility cases preserve both contextual banners and offer
follow-up. These are actual renderer bodies, not replacement implementations.

- Version the changed shared partner JS/CSS references in both public pages
  and the contextual JS references in the main page.
- Prewarm the same versioned URLs in shell v115.
- Treat the optional portrait helper as optional during an upgrade; company
  cards, branding and contact actions must still work with the earlier helper.
- Keep the existing cache policy. No global purge, cache disabling, paid
  metrics, auth change, SQL, photo publication, email or signing invitation.

Focused compatibility/directory/profile/banner/PWA run: 87 tests pass. The
test verifies the deliberately broken cached-helper case before asserting
recovery. Static contracts enforce matching page/worker versions and unchanged
cache headers. Exact-head CI and the existing intentional workflow supply the
complete regression before release. No document or signing map is touched.
Standing owner implementation/fix/merge/deploy authority applies. The Vercel
caching skill guided the bounded fix, preserving bandwidth-saving caching.

Release acceptance requires ordinary reload of the same canonical browser,
actual visible partner cards, unchanged outbound links and no phone overflow.
Do not substitute a fresh HTTP fetch for this returning-browser check.
