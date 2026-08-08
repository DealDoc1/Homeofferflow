# Production health import hotfix - 2026-08-08

## Scope

The canonical production read-only release check exposed a Vercel runtime
import failure in `/api/fill-pdf.py`: the production adapter could not import
the verified 20-19 source after the staging route was correctly excluded from
the production function bundle.

## Fix

- The production adapter now loads the verified implementation from the
  bundled `lib/verified_20_19.py` module.
- The staging source and bundled production copy are checksum-tested so they
  cannot drift silently.
- The bundle remains at exactly 12 Vercel Hobby functions; no staging route was
  promoted as a production function.

## Verification

- Full Python suite: **548 tests passed**.
- Vercel Hobby bundle test: passed at 12 functions.
- Canonical production release check: passed.
- Canonical production runtime reports:
  - release `18B-controlled-launch`;
  - main form `20-19 production`;
  - SignWell production mode (`signwell_test_mode: false`);
  - all required packet assets and fail-closed flags true;
  - public legal/PWA pages HTTP 200.
- Ready deployment: `https://homeofferflow-ecfiqxlrc-dealdoc1s-projects.vercel.app`

## Restricted-form boundary

This hotfix does not enable TXR-1501, TXR-1506, TXR-1507, or TXR-1508
production signing. Their completed signed-PDF visual QA gate remains intact.
