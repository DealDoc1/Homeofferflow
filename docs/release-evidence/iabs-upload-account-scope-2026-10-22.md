# IABS upload account scope and success state — October 22, 2026

## User outcome

Saving an IABS now shows the confirmed uploaded document without relying on a
second profile read. If the agent changes account, role, or account epoch while
the upload is in flight, the stale request cannot save metadata or render its
document into the newly active profile.

## Implementation and verification

- The upload captures the initiating user ID, role and account epoch. It checks
  that scope after the PDF header read, after Storage upload, and after metadata
  upsert; stale work stops before updating the active profile UI.
- After successful metadata upsert, the handler applies the exact saved payload
  to the current profile state and mounts the optional offer IABS control. It
  no longer waits for a second read that could fail after a successful save.
- Actual-source runtime checks: `node --test tests/agent_iabs_upload.runtime.cjs
  tests/profile_load_isolation.runtime.cjs tests/attachment_upload_isolation.runtime.cjs`
  — 45 passed. They cover the saved-profile success state, account switch while
  Storage is pending, file-signature rejection, upload routing and stale profile
  reads.
- Focused Python checks: `../txr1101-runtime/bin/python -m unittest
  tests.test_agent_iabs_profile tests.test_attachment_upload_isolation_runtime
  tests.test_uploaded_disclosure_workflow tests.test_saved_disclosure_attachment
  -q` — 24 passed.
- The PWA shell advanced to v124 so installed clients receive the updated
  account-scoped flow. `git diff --check` passed.
- Runtime fixture review confirms the saved profile card receives the persisted
  filename and the offer's optional IABS control mounts after success. No real
  profile, file or account was used.

## External-state and release boundary

No Storage object or metadata row was read or changed. This is implemented and
tested locally only; it is not deployed or production-verified.
