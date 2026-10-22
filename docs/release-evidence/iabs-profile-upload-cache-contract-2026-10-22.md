# IABS profile upload cache contract — October 22, 2026

## User outcome

Agents who select an IABS in the offer's generic Uploaded Documents section
now get routed to Profile > My IABS before packet-size checks; other selected
attachments can still be added. The private profile upload also sends the
cache lifetime value expected by Supabase Storage. The previous value,
`private, max-age=0`, was an HTTP cache directive rather than the Storage SDK's
numeric cache lifetime, and could make an otherwise valid PDF upload fail.

## Implementation and validation

- Generic packet attachments remain capped at 2 MB per file and 2.5 MB total;
  the IABS handoff is evaluated before those limits so a larger IABS receives
  the correct 10 MB profile-upload instructions.
- Changed only the IABS profile upload option to `cacheControl: '0'`; the object
  remains private at the existing `<user-id>/iabs.pdf` path and is still
  upserted with `application/pdf` metadata.
- Bumped the PWA shell cache to v116 so installed clients fetch the corrected
  app shell.
- Runtime tests invoke the actual profile upload handler and generic attachment
  handler, covering SDK options, metadata upsert, oversized-IABS guidance, and
  continued upload of a separate ordinary attachment.
- Two upload runtime suites — 20 passed.
- Uploaded-disclosure workflow plus six focused PWA/under-contract suites — 75
  passed.
- Full regression suite — 2,925 passed, 23 skipped. Updated the existing
  inline-feedback assertion to check the shared status wrapper introduced by
  the IABS routing, rather than requiring the old direct setter call.
- `git diff --check` — passed.
- Supabase's current JavaScript upload guide documents `cacheControl` as a
  file option and uses a numeric lifetime string such as `'3600'`:
  https://supabase.com/docs/reference/javascript/file-buckets-upload

## Remaining evidence gap

The user's original failed transfer was not captured, so this is a confirmed
Storage SDK contract defect and plausible cause, not a proven diagnosis of that
specific attempt. This checkpoint is implemented and locally tested only; it
has not been deployed or production verified. No customer PDF, account, or
stored document was accessed or changed.
