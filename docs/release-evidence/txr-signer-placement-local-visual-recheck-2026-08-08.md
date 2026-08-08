# TXR signer-placement local visual recheck

Date: 2026-08-08
Scope: TXR-1501, TXR-1506, TXR-1507, TXR-1508
Environment: local unsigned render only

## What was inspected

The four privately authorized source PDFs were rendered locally with representative
two-client data. Every page of each rendered form was inspected as a PNG. A
separate debug render drew the SignWell field rectangles over the printed form
to verify field, checkbox, initials, signature, and date placement against the
source lines.

The debug rectangles are QA-only and are not shipped or sent for signature.

## Results

- TXR-1501: all six pages render cleanly; the two-client page-6 signer boxes
  now sit on the client signature/date rows, and the broker-associate signer
  boxes sit on the associate row.
- TXR-1506: all six pages render cleanly; five-page consumer initials and
  page-6 broker/associate plus consumer signature/date boxes align with the
  printed acknowledgement/signature lines.
- TXR-1507: both pages render cleanly; page-1 initials align with the footer
  acknowledgement line, page-2 client signature/date rows align, and the
  broker-associate signer uses the associate row.
- TXR-1508: the one page renders cleanly; agent and one/two customer
  initials/date boxes align with the printed acknowledgement rows and do not
  sit in body text.

## Gate status

This is unsigned local visual evidence. It does not prove a completed
SignWell packet. Restricted TXR production enablement remains gated until an
authenticated one-client and two-client preview matrix is executed and at
least one completed signed PDF per form is downloaded and visually inspected.

No production deployment was triggered by this QA-only change.
