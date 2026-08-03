# Private TXR intake command — 2026-08-03

## What changed

Added `scripts/upload_private_txr_sources.py`, a repeatable local command for
the already-authorized TXR-1501, TXR-1506, TXR-1507, and TXR-1508 PDFs.

The command:

- verifies the expected filename, page count, and printed revision locally;
- supports `--inventory-only`, which needs no token or network request;
- requires an existing signed-in Supabase access token for destination
  selection and upload;
- requires an explicit active brokerage ID or slug;
- computes the exact PDF SHA-256 fingerprint;
- supports a safe authenticated `--dry-run`; and
- submits only through `/api/admin-dashboard`'s existing authenticated
  `upload_platform_form_source` action.

It never uses a service-role key, writes directly to Storage, inserts source
rows directly, or activates a workflow.

## Verification

- Dedicated uploader tests: 3 passed.
- Full repository suite: 386 tests passed on the current branch.
- Local inventory verification passed for all four supplied source PDFs.
- The command remains dry-run-first; restricted forms remain disabled until
  source-owner approval, signer-plan review, rendered-PDF QA, completed-signature
  QA, and release-authority approval are recorded.
