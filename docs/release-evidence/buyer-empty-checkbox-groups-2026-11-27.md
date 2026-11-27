# Correct the provider-confirmed buyer QA request rejection

## Provider evidence and bounded outcome

SignWell support replied to the owner-approved request in Gmail message
`1a21ee812f12cf19`, thread `1a21ee4a66323da6`, November 27, 2026.
Support traced request `66891bc3-8d08-493e-b2a4-83c051fb55a4` at
November 26 04:49:50 UTC. Their retained rejection names invalid_keys
[checkbox_groups]; the request supplied an empty array. They confirmed the
empty conditional_rules array was accepted, no document persisted from this
attempt, and no account/API restriction was responsible. This explains why
omitting the optional invitation message did not resolve the failure.

The isolated base is deployed `8e04cbb6aa959277b561a347d77b20a0b623fcb1`.
This is a protected operator QA correction, not activation of customer packages.
No schema migration, customer signing path, PDF renderer or field map changes.
No new paid service, preview or documentation-only deployment is required.
Automatic Git deployments remain disabled.

## Implementation and preserved boundaries

The new fixed recipe starts from the previous default-message comparison and
omits checkbox_groups only when the value is an empty list. Nonempty completion
controls remain intact. Conditional rules, explicit test/draft mode, parallel
recipients, exact reviewed source/packet/layout pins and the information-only
IABS remain unchanged.

It uses a distinct QA revision and document prefix. The original, canonical-wire
and default-message failure receipts remain untouched. The new owner/admin
control starts disabled until status is checked; its action accepts no custom
recipients, source IDs, packet settings or live/test override. It uses the same
reserve-once coordinator and private draft readback before any QA invitation.
Neither client acceptance nor a completed-provider buyer packet is claimed.

The coordinator now treats omitted optional group/rule arrays as empty for
receipt fingerprinting and readback comparison. It still rejects dropped
required flags, unexpected controls, moved fields, changed recipients or
unconfirmed responses. A new regression exercises both valid readback and
refusal to send after a required flag changes.

The value-free rejection classifier also retains exact known schema names from
errors.invalid_keys. Unknown names, URLs and provider text stay excluded. Its
public diagnostic shape is unchanged; this avoids losing the relevant field
name if a similar provider rejection occurs again.

## Focused and user-experience verification

49 focused checks passed, zero skips, with the actual pinned private sources:

```sh
python -m unittest tests.test_buyer_empty_groups_qa \
  tests.test_buyer_qa_release_boundary tests.test_buyer_representation_signing_qa \
  tests.test_buyer_package_qa tests.test_signwell_rejections \
  tests.test_signwell_qa_transport tests.test_operator_signing_controls_runtime \
  tests.test_operator_qa_create_rejections -q
```

HOF_BUYER_QA_SOURCE_DIR pointed at the preserved private source copies and
HOF_BUYER_QA_IABS_SHA256 used the existing reviewed pin. Full HTTP serialization
with MockTransport verified no checkbox_groups or message key, the exact PDF
SHA-256, all reviewed fields and explicit draft/test flags. No network/provider
request was made. PDF bytes and layout are identical to the reviewed specimen,
so no changed PDF pages require a new visual review at this checkpoint.

The actual operator UI function passed fixed-action/status tests for the new
scope alongside all existing controls. Functional review confirms the new
owner-only collapsed panel explains the correction and preserves failed
attempts. Live browser visual review is not claimed while the owner has the
separate Expo sign-in handoff.

Full candidate regression passed: 3,252 tests in 103.508 seconds with 30 skips,
using python -m unittest discover -s tests -q.

## Remaining release and provider verification

Commit and run fail-closed release preflight, protected CI, current Vercel
capacity/spend and normal intentional prebuilt deployment checks. Then use the
new fixed control once, verify persisted fields/controls and simultaneous QA
invitations, complete both nonbinding signatures with required disclosure
approval, and inspect the final signed PDF. Only then coordinate customer
package schema/code activation. Do not replay any of the three previous
reservations, create customer QA, or claim four enhancements deployed.
