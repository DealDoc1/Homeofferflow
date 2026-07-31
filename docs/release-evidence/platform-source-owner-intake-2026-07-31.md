# Platform source-owner intake evidence — 2026-07-31

## Scope

This change adds a platform-admin-only intake path inside the existing
`api/admin-dashboard.py` function for an exact, authorized source PDF. It is
intended for private source-owner handling when a brokerage has authority to
use a restricted Texas REALTORS® or other broker-owned form. Keeping it inside
the existing function preserves the Vercel Hobby 12-function cap.

The intake does **not** activate a workflow, render a packet, create signer
fields, send a document, or release a form to agents. Source approval remains
separate from signer planning, rendered-PDF QA, completed-signature QA, and
release authority.

## Controls

- Requires a valid Supabase session.
- Requires platform-admin authorization; a brokerage admin alone cannot use
  this intake endpoint.
- Limits the catalog to the currently reviewed form codes.
- Requires the printed source revision and an explicit authorization attestation.
- Requires a PDF header, a 10 MB size limit, and an exact SHA-256 match.
- Stores the PDF in the existing private `brokerage-form-sources` bucket.
- Records the source fingerprint, authorizing user, timestamp, and brokerage.
- Refuses duplicate active form/revision records.
- Returns `workflowActivated: false` and performs no signing or delivery.

## Current live state

The live OnDemand source vault remains empty until an authorized platform
administrator intentionally submits a source through this intake. No TXR form
has been activated by this change.

## Verification

- Platform intake parser and security-contract tests: 8 passed.
- Full repository test suite: run before commit and recorded in the release
  handoff.
- Deployment: intentionally not performed in this change; it will be bundled
  with the next approved production release under the Vercel Hobby deployment
  cap.
