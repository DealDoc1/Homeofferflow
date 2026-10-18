# Retained listing lead QA draft: read-only diagnosis

## Bounded workstream

- Outcome: identify exactly which verification differs in the existing fictional
  test draft, without creating another document, sending an invitation, relaxing
  a check or exporting signing credentials.
- Scope: the existing owner-only listing lead status action, a QA-only redacted
  diagnostic helper and focused tests. No signing map, PDF, customer interview,
  customer delivery path, database schema, billing or permissions change.
- Baseline: production `c2507e293cbb8cf11416c1e094438ec4e3541017`, verified by
  production run `39094550825` and canonical live owner-control use.
- Cost: automatic Git deployments stay disabled, no preview or new service;
  any intentional prebuilt release repeats existing spend/capacity checks.
- Evidence: fixed-spec authorization and no-write tests, redaction/malformed
  response tests, full frozen-candidate regression, exact-head CI, then an
  authenticated read-only status check on the same canonical live control.

## Implementation boundary

The existing check still requires the approved owner and platform-admin role,
the tracked document ID, fixed QA revision/layout/source, test mode and the two
approved QA inboxes. Caller-selected documents and fields remain impossible.
For a retained private draft only, it reconstructs the reviewed fixed packet
and returns check booleans, known field/group IDs and bounded scalar geometry
observations. Provider strings, values, names, email addresses, signing URLs,
metadata contents, regex text, credentials and exception bodies are not echoed.
Group ownership being null or a rule targeting a group is observed, **not**
treated as equivalent or accepted. The send verifier is untouched.

The read-only status action does not PATCH the tracker or POST to SignWell.
Repeated checks cannot create/send/resend a packet. Existing purchase, showing
and amendment controllers do not opt into this diagnostic. No browser cache
bump is necessary: only the uncached authenticated API response changes.

## Verification

37 focused readback, lead-QA, strict-controls and purchase-QA tests pass.
Malformed/nonfinite responses remain bounded and safe, sensitive provider
strings are not emitted, changed control/geometry checks remain false and
foreign test identity does not reach the diagnostic builder. Full regression,
CI, deployment and live diagnosis are not yet recorded as passed.

Frozen full local regression: **2,688 tests passed, no skips**, 87.305 seconds.
Expected mock transport/invalid-fixture messages are negative-test output, not
live provider failures. Patch whitespace is clean. No PDF or signing geometry
has changed, so no new rendered specimen or completed-provider claim is made.
