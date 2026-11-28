# SignWell support follow-up — sent

To: support@signwell.com
Reply in existing thread: 1a21ee4a66323da6
Status: sent after explicit owner approval, November 27, 2026 at 22:00:44 UTC
Gmail message: 1a21f066b21837d4; SENT independently confirmed by metadata readback
In reply to: 1a21ee812f12cf19; existing thread confirmed unchanged
No attachments, CC, BCC, credentials or customer data supplied

Hi Krijn,

Thank you for tracing the original failure. Omitting the empty checkbox_groups
key resolved document creation. We now have the following test-mode draft:

Document ID: fdaf5aae-6ddd-48af-a76d-d1dc0e2d4136
Name: QA ONLY - ordinary buyer package omit empty groups - 0e1e390bbd32
Date: November 27, 2026

GET readback confirmed the expected recipients, field placement, required
flags, completion controls, test mode and simultaneous signing settings.
However, our single POST to /api/v1/documents/{id}/send returned HTTP 422.
The document is still a draft. We have preserved it and have not retried.

The send request uses JSON with X-TestMode-Enabled: true and test_mode: true.
Its body contains only test_mode, name, subject, reminders,
apply_signing_order and metadata. It omits checkbox_groups and message.
Those options validate against your official SDK's send request model.

Could you trace the send request for this document and provide the exact
validation error, affected field, and required correction? Our diagnostic
retained the HTTP status but did not retain that response body. Please inspect
the draft without sending it or changing its recipients or signing fields.

Thanks,
Andrew
