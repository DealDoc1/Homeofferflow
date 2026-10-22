# IABS profile upload signature validation — October 22, 2026

## User outcome

The private IABS uploader rejects a mislabeled or unreadable file before it
stores the object or its metadata. Users get an inline recovery message while
the original upload path remains private and unchanged for valid PDFs.

## Implementation and verification

- `index.html` reads only the first four bytes and requires the `%PDF`
  signature, matching the existing purchase-attachment validation contract.
- Invalid signatures and header-read failures produce a clear inline error;
  neither reaches Storage or the document metadata upsert.
- Actual-source runtime checks: `node --test
  tests/agent_iabs_upload.runtime.cjs tests/attachment_upload_isolation.runtime.cjs`
  — 21 passed, including ordinary attachment routing and IABS-size guidance.
- The error state was reviewed in the runtime fixture: the inline status uses
  the existing error styling, names the problem, and tells the agent to choose
  the original brokerage-approved IABS PDF.
- `git diff --check` passed.
- Focused Python profile/attachment checks: `../txr1101-runtime/bin/python -m
  unittest tests.test_agent_iabs_profile tests.test_attachment_upload_isolation_runtime
  tests.test_uploaded_disclosure_workflow -q` — 19 passed.

## External-state and release boundary

No Storage object, metadata row, account, or customer PDF was accessed or
changed. This is implemented and locally tested only; it is not deployed or
production-verified.
