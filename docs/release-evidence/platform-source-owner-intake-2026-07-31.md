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
- Requires platform-admin authorization for this staging-on-behalf path. A
  brokerage administrator has a separate brokerage-scoped upload path with its
  own active-membership and exact-source attestation checks.
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
has been activated by this change. The deployed admin UI was verified on the
canonical site and the intake card is mounted only for the platform-admin
surface (with a compatibility fallback for older account shells).

## Verification

- Platform intake parser and security-contract tests: 8 passed.
- Full repository test suite: **317 passed**.
- Production deployment: `dpl_2rKWcB5VWgQDkSfdkW72TFWEcQeC`, commit
  `d202fc514dc6054097baf83a75a2e1174d9481c3`, state `READY`. Canonical
  verification: `https://www.homeofferflow.com/` returned HTTP 200 and
  contained the platform source-owner intake code.
- This was the single intentional deployment for the release, consistent with
  the Vercel Hobby deployment-cap policy.
