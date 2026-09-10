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

## Production and live signing verification

- PR [1192](https://github.com/DealDoc1/Homeofferflow/pull/1192) merged as
  `088147cdfed2919a1aa02cb3988b2097b66ae7ce`.
- [Production workflow 34499791510](https://github.com/DealDoc1/Homeofferflow/actions/runs/34499791510)
  passed all 1,619 regression tests, built on GitHub's standard Linux runner,
  and uploaded the prebuilt artifact to the existing Vercel project.
- Deployment `https://homeofferflow-dqoy8un52-dealdoc1s-projects.vercel.app`
  reached Ready at 16:06 UTC. Canonical site, PWA shell, API, and packet-runtime
  checks passed. This was not a paid Vercel remote build.
- Reopened the existing, unsent `QA ONLY Sep 10 Customer` TXR-1508 draft on the
  canonical site. The ordinary send screen visibly showed both the editable
  approved customer QA address and the read-only associate account address.
  No new draft or duplicate request was created. Account-specific addresses
  and provider identifiers are retained outside this public repository.
- Submitted the ordinary send form after confirming both addresses. The
  HomeOfferFlow queue changed to `sent` and SignWell independently showed
  the matching QA document as Sent, with the same two signer names.
- Delivery is sequential: customer first, then associate. Provider acceptance
  is verified; inbox delivery, execution, and completed-PDF placement are not
  yet verified. The assistant did not sign for either recipient.

## Additional UX follow-up from live purchase QA

- An already signed-in agent account retains its agent interview when entering
  through the homebuyer link; verify whether an explicit personal-purchase
  selection should override that saved role without changing account access.
- The closing screen showed an unrepresented-buyer concession tip alongside
  populated agent details. Correct the visibility rule in the next UX batch.
- Actual production CSS gave guided-form dialogs a transparent background
  because `--navy-dark` was undefined; their unscoped inputs had black text
  and a 17px height. Prepare a shared, responsive form-style correction and
  verify it with the complete production styles, not a simplified fixture.
- These are implementation follow-ups, not requests for user approval.
