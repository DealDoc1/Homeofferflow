# SignWell visual QA baseline — 2026-09-10

This record separates historical completed packets from the signer-map release
that they cannot validate.

## Completed-packet observations

| Form | Packet date | Result | Evidence |
| --- | --- | --- | --- |
| TXR-1507 short representation | 2026-09-09 | Pass for current one-client signer map | Broker and client signatures and dates render on the intended rows in SignWell packet `d6c614ce`. |
| TXR-1501 long representation | 2026-09-08 | Historical fail; not current-map evidence | Completed fields render detached from visible form content. Current map was recalibrated 2026-09-09/10. |
| TXR-1508 unrepresented showing | 2026-09-08 | Historical fail; not current-map evidence | Completed fields render detached from visible form content. Current map was recalibrated 2026-09-09. |
| TXR-1953 residential lease | 2026-09-05 | Historical fail; not current-map evidence | Buyer signature sits above rather than on its visible signature rule. Current map was recalibrated 2026-09-09. |
| TXR-1954 fixture lease | 2026-09-05 | Historical fail; not current-map evidence | Buyer signature sits below its visible signature rule. Current map was recalibrated 2026-09-09. |

## Required release verification

1. Deploy the current signer-map bundle once, intentionally.
2. Send controlled one- and two-party packets using the post-deployment code.
3. Complete, download, and visually inspect every signature, initials, date,
   and completion field against the source page.
4. Update the roadmap status only after those fresh packets pass.

Historical packets must not be used to justify a coordinate change after a
newer signer-map commit. Likewise, code/unit checks do not replace a freshly
completed SignWell visual inspection.

## Source-map check

The current source PDFs were rendered at 150 DPI and compared with the
top-origin 96-DPI maps. TXR-1953 buyer row one (`y=802`, `height=26`) ends at
the visible signature rule. TXR-1954 buyer row one (`y=774`, `height=26`) is
centered on the visible signature rule. This validates the current map
geometry only; it is not a substitute for a newly completed SignWell packet.
