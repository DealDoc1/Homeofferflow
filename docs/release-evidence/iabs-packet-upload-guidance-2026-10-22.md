# IABS packet upload guidance — October 22, 2026

## User outcome

When an agent selects an IABS in the transaction's generic Uploaded Documents
area, the status now says that the file was not added to this offer and
directs them to Account > Profile > My IABS. The handoff uses neutral
information styling so a supported routing rule does not look like a failed
upload. Other selected PDFs can still be added to the packet.

## Implementation and verification

- Updated the shared attachment handler's IABS guidance and status tone.
- The profile upload remains private and uses the Supabase Storage numeric
  cache lifetime option (`cacheControl: '0'`). Supabase's current JavaScript
  upload reference documents that option and demonstrates a numeric string.
- `node --test tests/attachment_upload_isolation.runtime.cjs
  tests/agent_iabs_upload.runtime.cjs` — 23 passed.
- `../txr1101-runtime/bin/python -m unittest tests.test_agent_iabs_profile
  tests.test_attachment_upload_isolation_runtime
  tests.test_uploaded_disclosure_workflow -q` — 19 passed.
- `git diff --check` passed. Source review confirms the guidance names the
  missing packet attachment and the next profile step; the focused runtime
  check verifies the neutral information tone and that unrelated PDFs still
  upload.

## Production and external-state boundary

- The latest Vercel production deployment record is READY at commit
  `3ed1ad5c11ff44294df160d0968dee117212344e`, whose merge message names the
  IABS upload reliability change. This confirms deployment metadata only; the
  current wording change in this checkpoint has not been deployed or
  production-verified.
- The available 24-hour Storage log sample contained two successful `200`
  requests and did not capture the user's reported failure. It cannot prove
  the cause of that specific attempt.
- No Storage object, metadata row, account, or customer PDF was read or
  changed. Automatic Git deployments remain disabled; the production release
  used the existing prebuilt workflow. No new deployment was created for the
  local follow-up.

## Follow-up local checkpoint

The IABS handoff now provides an **Open My IABS in Profile** button. Its action
saves the in-progress offer with the existing draft scheduler, opens the
Profile tab, and focuses the IABS upload input. The status remains a polite
live region, the route appears only for signed-in agent-side IABS selections,
and unrelated PDFs continue through the existing packet path. The service
worker advances to shell v127. `node --test
tests/attachment_upload_isolation.runtime.cjs tests/agent_iabs_upload.runtime.cjs`
passed 26 cases; the focused Python suite passed 66 checks, including PWA
cache/update paths, and `git diff --check` passed. This follow-up is implemented
and locally tested, not deployed; no external file, draft, or customer record
was changed.
