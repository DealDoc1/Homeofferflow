# Direct listing workspace handoff — 2026-09-21

## User problem

Production funnel data showed 15 sale-listing Question 2 views, only two task
choices, and one workspace opening. Agents had already chosen "Property
listing" in Question 1, but the product asked them to choose a listing task
again before they could enter the seller and property.

## Candidate change

- Continue directly from Property listing to the seller/property workspace.
- Keep Lease listing on the same direct path through one shared handoff.
- Preserve the necessary Question 2 choices for Purchase and Tenant
  representation, where the agent still must choose among materially different
  documents or packages.
- Record a privacy-safe direct-workspace event only after the property address
  question is actually available.
- Report direct sale- and lease-listing openings separately from Question 2
  conversion so the skipped question is never counted as viewed or selected.
- Add no dependency, vendor service, or recurring cost.

## Verification

- 113 focused agent funnel, activation, and handoff tests passed.
- Four transaction-routing runtime checks passed, including direct sale- and
  lease-listing readiness, delayed start measurement, and retained Purchase
  and Tenant representation questions.
- Full repository suite: 2,397 tests passed in 69.080 seconds.
- Python syntax compilation and patch whitespace checks passed.
- Deterministic production manifest: 142 files / 21,229,958 bytes.

## Release status

Implemented and locally tested. This improvement is not production-live until
it is merged and included in the coordinated post-reset deployment, followed
by authenticated canonical verification of both direct listing handoffs and
the new aggregate metric.
