# TXR-1507 client-reported placement correction candidate

## Status

**LOCAL CANDIDATE — not deployed and not completed-signature verified.**
Do not mark this map production-ready based on unit tests or synthetic previews.
The earlier completed-signature correction was insufficient. The two committed
geometry baselines remain unchanged until fresh provider-completed evidence is
reviewed; the two drift checks therefore intentionally report a mismatch.

## Confirmed finding

The owner supplied a real completed TXR-1507 on September 18. All three pages
were rendered and inspected, including its audit report. The original file
was read only; it was not modified, re-signed, canceled, replaced, or resent.
No client data, signatures, completed PDF, or source PDF is included here.

On the two-page 06-15-26 source, the shared first execution rule is at PDF
top-origin y=533.95, and the second client rule is at y=616.78. The preceding
map's first signature rectangle ended at (714+24)*0.75 = 553.5, below the first
rule. Completed date text measured about 49.21 PDF points wide, versus a field
width of only 36 points; the visible dates extended outside the execution area.
The completed document also showed high service/intermediary X marks and low
footer initials. GitHub main was read directly and contained the same candidate's
preceding 714/720-coordinate map; no claim is made about a live deployment SHA.

## Local changes

- First client and selected broker/associate signatures: y=684, height=24.
- First-row dates: y=692, height=18, width=72; shifted left to x=696 for clients
  and x=312 for the selected broker/associate.
- Second-client signature/date: y=794/802, same respective heights/widths.
- Client signature width reduced to 240 to keep separation from its date.
- Footer initials: y=976 and width=46, within each measured underscore blank.
- Service, intermediary, and selected role X strokes fit inside their source
  glyph cells, including stroke width.
- During showing-service preview review, the fee value was found on the prior
  sentence. It now uses its actual amount blank at PDF x=325, y=414.
- Form terms, recipient identities/roles, required-field flags, date format,
  source edition, and simultaneous-invitation behavior are unchanged.

## Verification and limits

- Four new independent source-bound tests cover one/two clients, broker and
  associate roles, full rectangles, readable date width, separation, initials,
  complete stroked X bounds, and showing-fee placement.
- 24 focused renderer/geometry tests pass after the correction.
- Full discovery ran **2,040 tests**: **2,038 pass; 2 geometry-baseline drift
  checks fail** because the reference maps have not been reapproved. This is
  not an all-green regression result. The other tests did not fail.
- The old map fails the independent execution bounds: its first field bottom
  is below the measured line and its date box is narrower than completed text.
- Generated local fake-name previews for both signer roles and both service/
  intermediary options using `scripts/qa/txr1507_execution_preview.py`.
- Visually inspected all four preview pages; rerendered and reinspected the
  showing-services page after correcting its fee blank. Rectangles and synthetic
  marks are legible and clear of captions. The PDF skill required this visual
  check in addition to geometry assertions.
- These are clearly labeled synthetic previews, not actual SignWell artwork.
  Fresh completed-provider QA remains required for signatures, dates, initials,
  and X marks before the map can be called verified.

## Next action and safety

Use a fresh controlled SignWell test packet, not the real client agreement,
then inspect its completed PDF against the measured bounds. Keep customer
replacement/re-signing separate; do not move signatures on the executed file.
Record the remaining provider check in the morning report. No publishing,
deployment, customer email, API send, or new paid resource occurred in this
correction pass. Existing publication/cost restrictions remain unchanged.
