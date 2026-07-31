# Agent IABS live-storage verification

## Scope

Read-only verification of the agent-owned IABS profile feature. This check
does not download, expose, or append the stored PDF to a new packet.

## Verified production state

- The private `agent-documents` bucket exists.
- The bucket is not public.
- The bucket accepts PDF files only and has a 10 MB size limit.
- The `hof_agent_documents` table exists and contains one IABS record.
- The stored object uses the exact per-agent path format `<user-id>/iabs.pdf`.
- The live record is classified as `document_type = 'iabs'`.

## RLS verification

The table has owner-only policies for select, insert, update, and delete. Each
policy compares `auth.uid()` to the row's `user_id`; updates also require the
new row to retain the same owner. No broker or platform dashboard policy grants
access to the PDF contents.

## Product behavior

- Agents upload or replace their IABS from their profile.
- Offer preparation asks **“Include my IABS?”** when a saved document exists.
- The option is off by default.
- The IABS is appended only when the agent explicitly selects it.
- The IABS receives no buyer signature fields and does not alter the offer
  packet's signing plan.
- Removing the profile document does not modify previously generated packets.

## Regression evidence

- Focused IABS/profile/storage tests: 43 passed with the brokerage and launch
  security tests.
- The complete release-worktree test suite remains green.
