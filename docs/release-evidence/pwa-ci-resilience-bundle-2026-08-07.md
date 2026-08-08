# PWA and CI-resilience bundle — release candidate

## Scope

This is a non-legal, non-form release candidate containing only installability
metadata and test-maintenance changes. It does not change offer generation,
PDF mappings, source PDFs, signer roles, SignWell delivery, billing behavior,
or Supabase data behavior.

## Commits

- `42e2b6a` — Harden PWA install metadata.
- `0c10217` — Make lifecycle tracker tests release-marker resilient.

## Exact files

- `manifest.webmanifest`
- `tests/test_pwa_baseline.py`
- `tests/test_subscription_lifecycle_tracker_reconciliation.py`
- `tests/test_tracker_reconciliation_2026_08_08.py`

## Verification

- Full local suite: **500 tests passed**.
- Targeted lifecycle tracker tests: **8 tests passed**.
- `git diff --check`: passed.
- `scripts/release_preflight.py --base 3abba8d --expected-deploy-author-email andrewchri@gmail.com`: passed; no packet/form source or mapping change detected.
- `main` is clean and pushed through `0c10217232e3e4cd934144fc28f5ce5a8fee0a26`.

## Deployment state

Not deployed yet. Automatic Git deployments remain disabled under the Vercel
Hobby-cap policy. This bundle should be included in the next intentional
production release after capacity is confirmed and the confirmation-gated
workflow is run for the exact `main` commit.

## Post-deploy checks

1. Confirm the canonical manifest is served from `https://www.homeofferflow.com/manifest.webmanifest`.
2. Confirm the home page remains HTTP 200.
3. Confirm authentication, offer generation, signing, billing, and the
   restricted-form gates remain unchanged.
