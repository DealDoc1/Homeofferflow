# Direct tenant agreement choice — 2026-09-21

## User problem

Production funnel data showed four Tenant representation Question 2 views and
no package choice, document choice, or workspace opening. The agent had already
chosen Tenant representation in Question 1, but the next screen repeated that
decision by asking whether to create a representation agreement or a showing
form / consumer notice.

## Candidate change

- Continue directly from Tenant representation to the meaningful short-form or
  detailed representation-agreement choice.
- Preserve the full Question 2 interview for Purchase, where materially
  different document families still require another decision.
- Record a privacy-safe direct-question event only after the agreement choice
  is visible and a direct-workspace event only after the selected document
  interview is open.
- Report direct tenant handoffs separately from sale- and lease-listing
  handoffs and from the retained Question 2 funnel.
- Add no dependency, vendor service, or recurring cost.

## Verification

- 117 focused agent funnel, activation, abandonment, and navigation tests
  passed.
- 16 browser-runtime navigation and transaction-routing checks passed,
  including direct tenant agreement selection and retained Purchase Question 2.
- Full repository suite: 2,398 tests passed in 71.982 seconds.
- Python syntax compilation and patch whitespace checks passed.

## Release status

Implemented and locally tested. This improvement is not production-live until
it is merged and included in the coordinated post-reset deployment, followed
by authenticated canonical verification of the tenant agreement handoff and
the new aggregate metrics.
