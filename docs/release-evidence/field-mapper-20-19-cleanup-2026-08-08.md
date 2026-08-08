# Internal field-mapper 20-19 cleanup - 2026-08-08

## Scope

The internal `field-mapper.html` developer tool was updated to identify the
current TREC 20-19 contract instead of the obsolete 20-18 contract. The
change updates the visible upload guidance and the names of generated debug
files only.

## Release classification

- Developer-tool/documentation change only.
- No production offer route, PDF template, field map, signer plan, or packet
  assembly logic changed.
- No restricted Texas REALTORS® workflow was activated.
- No Vercel deployment is required for this isolated cleanup; it is bundled
  for the next intentional release.

## Verification

- `git diff --check`: passed.
- Full Python regression suite: 513 tests passed on 2026-08-08.
- Deterministic production bundle manifest: 
  `vercel-production-bundle-manifest-2026-08-08.json`.

