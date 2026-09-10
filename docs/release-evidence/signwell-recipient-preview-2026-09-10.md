# Complete signing-recipient preview — September 10, 2026

## Why this correction is needed

The standalone send screen displayed only customer email inputs even when the
stored signer plan also includes the agent or broker. The server already
resolved that additional signer, but the UI did not show the complete delivery
list. A controlled live send was stopped by safety review before submission.

## Changes

- Resolve every signing contact through the same server-side recipient builder
  used for delivery. Return only labels, names, email addresses, and editable
  email indicators for one authenticated agent's own unsent draft.
- Show account-linked associate or broker contacts as read-only recipients in
  the existing send screen. No extra customer approval checkbox or workflow
  step is added.
- Compare submitted confirmation against the server's current recipient list
  before source download, PDF generation, or SignWell delivery. Changed,
  missing, additional, and reordered recipients are rejected.
- Require a distinct email for every signer, including the agent/broker.
- Keep existing signer roles, PDF coordinates, source editions, signing order,
  access rules, and account permissions unchanged. No database migration.

## Verification

- Full local suite: 1,619 tests pass, including ten new recipient-preview and
  confirmation tests. All 43 inline JavaScript blocks parse; whitespace clean.
- Ownership and unsent-status filters are asserted at the data query boundary.
  An unavailable draft or invalid identifier cannot expose signing contacts.
- A synthetic localhost browser check displayed both customer and associate
  with the actual production dialog implementation. Its submitted JSON
  contained the complete visible list and reached localhost only.
- A second local browser case rejected a duplicate customer/associate email.
- Unit tests verify an unconfirmed send stops before downloading source files
  or creating an external SignWell client.

Production deployment and the subsequent live send are recorded separately.

## Additional UX follow-up from live purchase QA

- An already signed-in agent account retains its agent interview when entering
  through the homebuyer link; verify whether an explicit personal-purchase
  selection should override that saved role without changing account access.
- The closing screen showed an unrepresented-buyer concession tip alongside
  populated agent details. Correct the visibility rule in the next UX batch.
- These are implementation follow-ups, not requests for user approval.
