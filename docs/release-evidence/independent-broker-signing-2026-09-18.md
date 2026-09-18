# Independent broker signing - September 18, 2026

**Local candidate only. Not deployed or live-provider/database verified.**

## User-facing result

An agent who selected a broker signer can enter the broker's name and email on
the existing recipient-review screen when no own-office broker contact is
available. No brokerage seat, source-owner contact, approval or additional page
is required. Existing account-associate signing is unchanged. Linked-office and
saved-request contacts remain read-only on this screen.

Broker inputs appear together on desktop and stack on mobile. Required-field
validation, email validation, exact recipient review and duplicate-address
checking apply before sending. Entered details remain in the open dialog after
a failed attempt; successful completion closes it normally. Client addresses
are separated from the professional recipient, so the newly editable broker
email cannot accidentally be counted as another client.

## Server and recovery behavior

- The owned draft's signer plan controls whether a broker can be entered. A
  request cannot add a broker to an associate or buyer/seller-only document.
- Name/email are validated and normalized; malformed input, overlong values,
  control characters and duplicate signing emails are rejected.
- The entered broker cannot silently replace an existing own-office contact.
  The form-source brokerage never supplies the recipient.
- The reviewed contact is saved in `agreement_data.broker_signer` with the
  existing owner/version-scoped signing checkpoint, before invitation delivery.
  This needs no schema migration or new service.
- Retry restores that contact and uses the same tracked request. A repeat of the
  same entered details is accepted; changing a saved contact is rejected. The
  broker is not inferred from the agent's email or the source owner.
- Both the recipient list and the resolved professional context bind the
  contact to the request fingerprint. The persisted contact's duplicate is
  excluded only from the overlay-answer portion, avoiding first-send/retry
  mismatches without weakening recipient binding.
- Simultaneous signing remains enabled (`apply_signing_order=False`). No form
  geometry, source wording, existing client PDF or signer's signature is edited.

## Verification

- 43 focused Python methods pass. New cases include editable no-seat preview,
  locked saved contact, all four professional form role variants, malformed
  input, unexpected-role and linked-office replacement rejection.
- Real-render/offline-delivery integration covers TXR-1501/TXR-1507, one/two
  clients, saved broker persistence, rendered brokerage identity, duplicate
  addresses, saved-contact tampering and recovered retries. Reconciliation of
  an already-sent test provider record creates no second document/invitation.
  HTTP/database callbacks are test doubles, not production evidence.
- The actual send-dialog function, escaping helper and dialog styles run in a
  real isolated headless browser at 390px and 1280px. Tests verify required
  fields, duplicate rejection, exact payload, retry input retention, read-only
  saved contact, successful close, no horizontal overflow and no JS errors.
  Both desktop/mobile screenshots were visually inspected. All page network
  routes were blocked and fetch responses were synthetic.
- All 45 inline page scripts parse successfully.
- Final full discovery: 2,229 tests in 50.219 seconds; 2,227 pass. The same two approved signing-map
  reference comparisons remain unresolved. No baseline was regenerated.
  Log: `/private/tmp/hof-independent-broker-suite.log`.

The browser skill informed real-browser and responsive verification. Its
`agent-browser` executable was unavailable, so bundled Playwright used a fresh
headless Chrome context; no user profile or user tab was accessed, and the
browser closed in a finally block. Private screenshots are untracked under
`tmp/qa/independent-broker/`.

The Supabase skill informed the persistence/security review. Current changelog
and Data API security guidance were rechecked. Existing verified-user ownership
and conditional update predicates remain unchanged; no editable metadata grants
authorization, no client keys/grants/RLS/schema changed, and no live database
query or mutation occurred. Production verification remains outstanding.

No push, deployment, Vercel build, customer invitation, live provider request,
paid test or additional resource was made. Source-PDF footer branding and the
broader completed-provider placement review remain separate outstanding work.
