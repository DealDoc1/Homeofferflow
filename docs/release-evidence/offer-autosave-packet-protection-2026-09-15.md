# Offer autosave and revision protection — local verification

## Scope and observed defect

The browser draft writer used cached signing state to write `status`, provider IDs,
generation timestamps, and the full `offer_data` object. A stale tab could downgrade
a sent/signed offer to Generated or remove its delivery journal. The existing copy
operation also retained `_hof_signature_delivery` and several provider-status fields.

## Implemented

- Draft saves no longer write packet status, signing IDs, or generation timestamps.
  They read the current owned, nondeleted row and use a `last_updated` comparison
  for the update. A changed version is not reported as successfully saved.
- Prepared packets are not edited in place. Resume opens a new editable copy;
  copies retain answers but strip signing/delivery history and, as before, exclude
  previously uploaded disclosure attachments.
- An already-open tab whose packet has since been prepared keeps its edits locally
  and offers “Save changes as a new draft.” That action retains the current answers
  and removes the old packet identity. It sends no invitations and does not generate
  or charge for a new packet.
- Manual retry shares the existing save lock instead of starting an overlapping save.
- The migration protects prepared rows from authenticated/anonymous client updates,
  including clients running older JavaScript. It protects all answer/packet columns,
  recognizes legacy JSON-only signing IDs, and permits the existing explicit soft
  delete without allowing answer changes to accompany it.
- New browser inserts cannot manufacture signing state or copy a delivery journal.
  Service-role generation, delivery checkpoints, and webhook updates remain allowed.
  The trigger is security-invoker with a fixed search path; no public RPC grant,
  role escalation, new user approval, brokerage-seat requirement, or paid dependency.

## Verification

- Actual browser JavaScript executed in Node: stale signed-state detection, draft
  version matching, failed update handling, clean new inserts, legacy provider IDs,
  one clean copy on resume, and retaining edited terms through the recovery action.
- Isolated PostgreSQL (PGlite): **19 checks passed**, using the repository baseline
  `hof_offers` table and a synthetic ownership policy. Includes nullable-status attacks,
  rejected receipt/answer overwrite, service-role updates, legacy records, soft delete,
  function privileges, and owner isolation.
- Full Python test suite: **1,966 tests passed**. The printed “Invalid fixture PDF”
  diagnostic is an intentional negative test, not a test-suite failure.
- `git diff --check`: passed.

This is not live Supabase/PostgREST, multi-connection, or production browser QA.
The local Supabase security advisor could not connect to the absent local stack
at port 54322; it is **not recorded as passed**. Current changelog and trigger docs
were reviewed; no relevant breaking change was identified.

## Release status

Local only. No push, migration application to production, Vercel deployment,
customer-email send, SignWell operation, or paid hosting usage was performed.
Apply the migration together with the client release, then verify draft editing,
copy/edit, signing recovery, and soft deletion against the real ownership policies.
The migration protects already-open older clients, but their new-draft recovery UI
requires refreshing to the updated client. Existing packets were not modified.
