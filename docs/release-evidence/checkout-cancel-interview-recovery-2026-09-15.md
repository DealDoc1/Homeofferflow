# Cancelled checkout restores the interview and intended files

## Confirmed problem

The cancelled-checkout return copied `hofOfferData` into `state.data` but did
not hydrate the interview's DOM controls. It then opened payment review.
The next collection of interview values could therefore replace the recovered
answers with blank or previous values. Available session attachments were not
restored to the active upload list either.

Separately, `validateUploadedDisclosureDocs()` returned true for an empty active
upload list even when saved filenames showed that intended attachments were
missing. Re-uploading only one missing PDF replaced the saved filename list,
silently forgetting the others. Legacy `uploadedDocs` bytes could also survive
a restore and be used by the backend's compatibility fallback.

## Changes

- Cancelled buyer checkout now uses the existing complete field hydrator,
  restores the receipt email and selected plan, and reopens payment review.
- Available files from the same tab's checkout snapshot are restored in order;
  another transaction's in-memory files are cleared. The existing attachment
  review acknowledgement is reset. No extra approval requirement is added.
- Snapshot restoration rejects unrelated agent/investor snapshots and strips
  old generated/signing state and offer identity. Local-draft fallback now
  requires the homebuyer role while retaining existing account-owner checks.
- Missing attachments prevent payment/generation from silently omitting them.
  The interview opens the existing upload step and focuses its file input.
  Users can reattach the PDFs or deliberately choose **Remove missing files**.
- Partial re-uploads and removal of a present file preserve other missing
  filename reminders. Ordinary resumed drafts retain names, not stale file
  contents in either current or legacy attachment fields.

## Evidence

- 89 actual-source Node interview/restore cases pass, including eight added
  cancelled-checkout/attachment cases. These execute the real field hydrator,
  return handler, filename validation and upload handler with a mocked DOM.
- Against `ed0d2247`, the cancelled-checkout test fails specifically because
  `propAddress` remains `Wrong previous property` instead of `Current property`.
- Full local suite: **2,028 tests pass in 18.000 seconds**. The Node cases run
  through the existing Python wrapper, so they do not each add a Python count.
- All 45 inline script blocks parse; `git diff --check` passes.

## Limits and next work

Local only; not pushed or deployed. No Vercel build, live checkout, customer
email, signature or customer-record mutation occurred. Node DOM tests are not
visual browser or production end-to-end QA.

The existing session-storage write can still throw if browser storage is full
or denied. That separate pre-checkout persistence failure remains to address;
this change does not claim to fix it. Same-tab cached attachment restoration
does not add cross-device attachment persistence.
