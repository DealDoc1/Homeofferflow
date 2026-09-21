# Lease addendum completed-PDF QA and field correction — September 15, 2026

## Actual completed-document review

The existing authenticated SignWell workspace was used to open and download
these controlled test packets. Both form pages and both provider audit pages
were rendered and visually inspected. No new invitation was sent.

Exact provider references, PDF fingerprints, and downloaded specimens are
retained in the operator's local private QA evidence, not this public repository.
No signed PDF, signature artwork, recipient contact, or download URL is included.

Both audit pages record buyer and seller completion on September 11, 2026.
Each packet contains one Buyer and one Seller, not two of either party and not
the combined purchase packet. Signatures sit above the correct printed rules
without covering captions. No signature coordinate change is warranted by
these two specimens.

**The completed forms do not pass overall field-placement QA:** the selected X
marks extend above their boxes. TXR-1954's address touches the printed rule.
Those findings supersede the stale tracker instruction to wait for these two
standalone documents to finish signing. Their audit trails also show the old
sequential invitation flow; they are not simultaneous-invitation evidence.

## Local corrective implementation

- Both renderers now center compact six-point X marks on source checkbox
  centers, covering all status, fixture, assumption, removal, and delivery choices.
- TXR-1954's address baseline is raised three points above the rule.
- The expanded conditional review found TXR-1953's termination-day count
  overlapping printed sentence text, and oral-notice/explanation text below
  their rules. Those overlays now use their actual printed blanks.
- Signer roles, signature rectangles, form wording, and source editions are
  unchanged. No new access or approval requirement is introduced.
- Rendering revisions are recorded in standalone provider metadata and in
  the integrated offer recovery fingerprint, so earlier document contents are
  not mistaken for this correction.

## Source and visual checks

User-supplied source editions: TXR-1953/TREC 51-1 and TXR-1954/TREC 52-1,
both 11-07-2022. Private source bytes remain out of Git.

Source fingerprints are retained with the private QA evidence.

Seven local source-backed scenarios were rendered and visually inspected:
residential termination, assignment/received, assignment/not-received,
assignment/oral-notice with explanation; fixture inventory/assumption with all
choices, will-remove/not-received, and oral-notice. These exercise every checkbox
position and the corrected text blanks, with signing lines left clear.

Seven added regression tests inspect actual PDF drawing operations, including
every checkbox center, day-count and narrative coordinates, the address
baseline, and render-revision fingerprint changes. Full local suite: **1,855
tests passed**. All **12 core golden packet scenarios** still match their
approved rendering baselines. Signature geometry is unchanged.

## Release boundary

Local correction only, stacked on PR #1233. No Vercel build, preview or deploy;
no real customer record, existing signed document, or subscription changed.
The original completed PDFs remain immutable defect evidence. A fresh completed
PDF using the corrected render is still required after release, along with
two-Buyer/two-Seller and combined-purchase-packet coverage. Do not mark the
overall Paragraph 4 roadmap items complete from these narrower specimens.
