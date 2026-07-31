# HomeOfferFlow mobile-app product brief

## Current position

HomeOfferFlow is already responsive and installable as a web/PWA experience.
That remains the supported mobile product while the agent, brokerage, and
subscription workflows stabilize. A native companion app is a later release,
not a second authorization system or a shortcut around the web release gates.

## Product goal

Provide an agent-first iOS and Android companion app for the work agents do in
the field:

- sign in and resume an authenticated agent workspace;
- create, save, duplicate, and update buyer-offer drafts;
- view offer and electronic-signature status;
- receive bounded status notifications;
- open the existing mobile-safe offer interview and document review surfaces;
- access private profile documents such as an agent's IABS only through the
  same owner-scoped rules as the web app.

## Explicit non-goals for the first native release

- no new buyer, seller, or broker data access;
- no local caching of complete offer packets or private source PDFs by default;
- no native legal-form implementation separate from the approved web workflow;
- no bypass of brokerage membership, TXR/NAR attestation, subscription, or
  completed-signature QA gates;
- no platform-admin or broker-wide buyer-sensitive data in an agent app.

## Architecture direction

1. Reuse Supabase Auth and the existing server/API authorization model. The
   native client must never contain a service-role key.
2. Reuse the existing RLS-protected tables and server endpoints rather than
   duplicating offer, brokerage, IABS, or signing state in a new database.
3. Use short-lived sessions with refresh-token protection supplied by the
   platform's secure credential storage. Sign out must clear local session
   material and any cached non-sensitive metadata.
4. Treat push tokens as user-owned records with revocation and device metadata;
   notifications contain status summaries, not buyer names, addresses, offer
   terms, or document contents.
5. Keep document rendering and signing orchestration server-side. The app may
   open a controlled review/signing surface but must not invent fields or
   create an alternate signer plan.

## Delivery phases

### Phase 0 — PWA hardening

- verify mobile breakpoints, install metadata, safe-area behavior, and upload/
  download behavior on current iOS and Android browsers;
- complete brokerage-admin, billing, and golden-packet regression coverage;
- define the mobile threat model and data-retention policy.

### Phase 1 — Authenticated shell

- build a thin agent-first shell using the existing auth and API contracts;
- support sign-in, profile, offer list, and signing-status read-only views;
- add device/session revocation and crash-safe logout QA.

### Phase 2 — Field workflow

- add draft creation, resume, duplication, and bounded document review;
- preserve web/API parity and run the existing rendered-PDF golden suite;
- test poor connectivity without silently submitting stale terms.

### Phase 3 — Notifications and store release

- add opt-in push notifications for signing/status events;
- verify notification redaction and per-user/brokerage authorization;
- complete iOS/Android device QA, accessibility QA, privacy review, and store
  release checklists.

## Release gates

The app cannot be promoted until the web suite remains green, Supabase RLS is
verified for every mobile-read table, notification payloads are redacted,
offline behavior is documented, and mobile UI plus offer/signature regressions
are tested on representative iOS and Android devices. Legal-form releases
retain their separate private-source, signer-plan, rendered-PDF, completed-
signature, and HomeOfferFlow release-authority gates.
