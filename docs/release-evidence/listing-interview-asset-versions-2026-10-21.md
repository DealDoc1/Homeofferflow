# Listing interview asset versions — October 21, 2026

## Outcome and scope

Keep a returning browser or installed shell on the reviewed sale/lease interview
assets after a future release. This is preventative hardening in the customer
listing candidate, not a diagnosed current-production failure. Inspection of
production main 0b50b3b5 confirmed these three interview files are new to the
candidate; there is no older live listing script to claim was already stale.

Use the first 16 hexadecimal characters of each unchanged file's SHA-256 as its
query version in both index.html and the shell prewarm list:

- Sale/shared interview JS: 3a6e25ef4244900d.
- Lease model JS: 139d5b063c6b227e.
- Shared interview CSS: 73c0decf7c4321c8.

The lease model still loads before the shared engine. The fixture generator now
extracts the actual source-page asset references instead of hardcoding unversioned
ones. Tests bind every URL to the real bytes, so later asset edits require an
updated version. Existing caching headers and unreleased shell v116 stay intact;
no global purge, caching disablement or customer content change.

## Verification

- New guard first failed against the unversioned candidate, as expected. Its
  failure messages were then bounded to avoid dumping the entire HTML file.
- `python -m unittest tests.test_listing_asset_versions
  tests.test_txr1101_interview_runtime tests.test_txr1102_interview_runtime
  tests.test_partner_asset_versions`: 18 passed.
- PWA-focused discovery: 69 passed. Whitespace clean.
- Real browser, isolated localhost fixture with fictional data and external
  connections blocked: lease entry directly opens step 1 of 7; sale opens step
  1 of 6. All three fingerprinted files returned HTTP 200 on the first page and
  HTTP 304 on the second. No JavaScript errors were observed.
- Private screenshots: `../listing-cache-2026-10-21/lease-versioned-assets.jpg`
  and `sale-versioned-assets.jpg`. They show local fixtures, not production.
- This fixture does not serve a service worker (its registration request returns
  404). Therefore no browser-installed-worker/offline claim is made; matching
  shell asset references are checked programmatically only.
- Actual interview JS/CSS bytes, PDF renderers and signer maps are unchanged.
  No save, provider send, hosted SQL, billing mutation or real customer data.
  Temporary tab closed and loopback server stopped.

## Release state

Locally tested only. The exact-head CI success 39676225172 (3,039 tests, 29 opt-in
skips) still applies to 45ff824b, not this later asset-reference change. Do not
claim this new checkpoint has full exact-head CI until the next candidate freeze.
No CI push or deployment is needed merely to repeat that earlier verification
while the existing final-signature consent and completed-PDF review are pending.
