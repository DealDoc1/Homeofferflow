# Seller/listing disclosure upload hardening — 2026-08-03

## Release scope

This release hardens the existing agent-supplied PDF attachment path. It does
not generate, interpret, or sign a seller disclosure, listing agreement, or
other seller-side legal form.

## Behavior verified in code

- An agent may upload up to five PDF attachments, each up to 15 MB.
- Each attachment is labeled as a seller disclosure, survey/T-47, HOA/POA
  document, PID/MUD notice, lead-based paint disclosure, or other document.
- The agent can move attachments up or down so the final packet order is
  deliberate and visible.
- The agent must confirm that the PDFs, labels, order, and authority to include
  them were reviewed before checkout or subscribed packet generation continues.
- The existing backend appends the validated PDFs after the generated offer
  packet and keeps the supplied order.

## Verification

- `tests.test_uploaded_disclosure_workflow`: passed.
- `tests.test_controlled_launch`: passed, including uploaded disclosure packet
  assembly and SignWell field page offsets.
- Full regression suite: run as part of the release gate.

## Boundary

Seller disclosure generation, listing agreements, seller-side checkout, and
seller-side signing remain source-gated and are not enabled by this release.
