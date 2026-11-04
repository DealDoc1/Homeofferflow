# Check committed whitespace in PR CI — November 4, 2026

The buyer QA release exposed a real CI gap: PR tests ran git diff --check
against a clean runner checkout, so a newly committed file's extra blank line
passed CI. The stronger production workflow compared the actual release range
and correctly stopped before deploying (run 41843347566).

The ordinary test workflow now checks explicit immutable base/head SHA pairs:
pull-request base/head for PRs, and before/current SHA for main pushes. Checkout
fetches history so both revisions are available. The check runs immediately
after checkout, before dependency installs or tests, so bad commits fail cheaply. Invalid, missing or unavailable
commits fail closed; an initial push with an all-zero before SHA also fails
instead of silently checking an empty range. No live application behavior,
permissions, secrets or production release check is changed.

Five focused tests execute the actual workflow shell block against temporary
Git repositories. They reproduce the original committed new-file EOF error on
a clean checkout (the old check passes; the new one fails), accept a clean
committed range, catch an earlier bad commit hidden by a clean final commit,
reject missing/invalid/unavailable references and verify both event mappings.
Command: txr1101-runtime/bin/python3 -m unittest
tests.test_ci_committed_whitespace -q. Five tests pass. No network is used by
these tests, and no new dependency/service is introduced.

Implemented and focused-tested locally. The active QA-only production release
remains frozen at its separately tested commit. This workflow improvement needs
its own normal PR/CI review; it needs no Vercel deployment. The full application
suite is not repeated locally for this CI-only change. No customer/partner
message, provider request, schema change, charge or new automation was made.
