# Production release baseline hardening - 2026-08-08

## Scope

The intentional production workflow now resolves a push-triggered release's
preflight base from the most recent prior `[deploy-production]` commit instead
of comparing only with `HEAD^`. This prevents an empty marker commit from
concealing earlier packet, field-map, signer-map, or restricted-form changes.

## Verification

- Commit: `e9feeb3` (`Harden production release baseline detection`)
- Local full regression suite: **537 tests passed** with the bundled Python
  runtime and pinned HTTP client dependency.
- Release-base resolver test: prior marker resolved; missing marker fails
  closed.
- Production workflow contract tests: passed.
- `git diff --check`: passed.
- Current resolver output: `0c66ef37a856ee566e3043de7de01a8143b4f5f3`.

## Deployment boundary

This change does not activate any restricted legal-form workflow and did not
trigger a Vercel production deployment. Supported production workflows remain
unchanged. Restricted TXR activation still requires authenticated one- and
two-client previews and completed signed-PDF visual inspection.
