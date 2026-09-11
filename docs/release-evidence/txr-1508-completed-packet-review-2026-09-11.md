# TXR-1508 completed-packet visual review — 2026-09-11

## Scope

- Form: TXR-1508 Unrepresented Customer Showing Form, revision 02-25-26.
- Reviewed artifact: completed controlled SignWell packet `2a66cbf5-1618-471c-b354-2458353bd9b0`.
- Review method: visual inspection of the completed PDF's form page and audit
  report, followed by a source-specific current-map overlay against the
  approved private TXR-1508 source.

## Finding in the reviewed completed packet

The packet was created on September 10, 2026 at 16:10 UTC. Its agent
acknowledgement date is visibly rendered in the printed license-number area,
rather than on the acknowledgement date rule. The agent initials and customer
initials are also visibly high relative to their printed rules.

This is failure evidence for the map that created this completed packet. It
must not be described as passing signature-placement QA.

## Current source-map preflight

The current `lib/txr_1508.py` map was changed after that packet was created.
A local overlay of the current fields on the exact private TXR-1508 source
places the agent and customer initials and date rectangles on their respective
printed acknowledgement rules. The preflight also confirms that the compact
acknowledgement checkbox mark remains within the source cell.

That local result is geometric preflight only. It does not claim that SignWell
has rendered a corrected completed packet.

## Required next proof

Create and complete one new controlled TXR-1508 packet using the current
release. Visually inspect the completed PDF for these facts:

1. agent initials are on the agent acknowledgement rule;
2. agent date is on the agent Date rule, not either license-number field;
3. each customer initials and date value stays on its own printed rule; and
4. no field overlaps the representation-agreement acknowledgement text or
   checkboxes.

The old packet remains retained as the before-correction visual finding.
