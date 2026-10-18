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

## Observed production result

PR #1347 merged as `61e516d0a091646bbff14a00624051d4e328d4fc` after exact-head
CI `39130025986` passed. Intentional production run `39130371738` passed at
2026-10-18 13:13:36 UTC. CLI inspection independently confirms production READY
deployment `dpl_2agZyywm1ahG4Pk5tjdaWdZ3YfVx`, canonical domain aliases and
the existing project. The release spend check reported $0.05 infrastructure
usage, $19.95 unconsumed and a $3 reserve. A bounded error-level runtime scan
returned no logs; that is not a guarantee of future behavior.

The authenticated canonical owner check returned true for every identity,
parallel-invitation, metadata, field-set, geometry/recipient, checkbox-group
and conditional-control check on the **original** v1 draft. The initial
immediate-readback failure's exact cause is not established. No nullable-owner
normalization, conditional-rule weakening or plan upgrade was needed.

After that passing readback, the existing exact QA tracker row was conditionally
advanced to `send_started`, with the controls-verification receipt saved before
the provider action. The existing SignWell session was restored by its normal
Google sign-in. The send dialog confirmed the two approved inboxes, parallel
invitations, reminders off and the unchanged explicit fictional-test message.
The original draft was sent **once** through the provider UI. The provider
displayed "Your Document Has Been Sent!"; the canonical owner status independently
confirmed it was awaiting completion in the two approved inboxes. Tracker run
`03d45107-ccb6-4dac-92e0-741282f53eb2` was conditionally reconciled to `created`,
provider `sent`, test mode true, then SELECT-verified. No replacement draft,
new subscription, customer message, permission or schema change occurred.
Gmail independently confirms the first QA invitation arrived at 13:16:31 UTC,
message `1a14f281fb55ffa5`, with the same document ID in its provider header.

## Actual signer finding - not passed

SignWell explicitly displayed test mode / not legally binding. In the first
signer session, four choice groups enforced exactly one selection. Selecting
known hazards/no reports in the first case and no knowledge/reports provided
in the second required only the two corresponding explanation fields.

Typing a 200-character fictional explanation exposed a real presentation
failure: the text field grew from its requested 73.333px height to 687px
provider CSS height (approximately 791px at the current displayed zoom).
It retained the same oversized type and height after blur. This is a failed
live explanation-layout check, not a completed-signature pass. No signature,
electronic-disclosure acceptance or Agree & Finish was performed. The packet
remains a useful retained failure specimen; do not resend it or ask the owner
to finish this flawed revision. See the separate v2 text-layout checkpoint.
