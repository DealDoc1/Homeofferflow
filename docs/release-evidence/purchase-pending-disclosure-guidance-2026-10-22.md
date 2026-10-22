# Purchase packet pending-disclosure guidance — October 22, 2026

## User outcome

When the optional seller disclosure cannot be included in a generated purchase
packet, customers see a dedicated completion-screen notice that explains the
omission, where to finish or review the disclosure, and that it cannot be added
to the already-generated packet. The notice does not imply that the other
documents failed or that the disclosure was included.

## Implementation and validation

- Added a separate accessible status notice to the existing offer completion
  screen. It appears only when packet generation succeeded and the API reports
  pending documents; otherwise it is hidden and cleared.
- Kept the current API response and delivery/signing summaries unchanged. The
  notice directs agents to **Listing Tools** to finish or review the disclosure
  and send it separately; it cannot be appended to this packet later.
- Advanced the offline shell cache to v120, above the current production v116
  and the unreleased partner candidate's v119.
- Focused validation: `python3 -m unittest tests.test_packet_delivery_summary
  tests.test_pwa_baseline tests.test_pwa_update_experience -q` — 35 passed.
- Full regression on this exact candidate:
  `PYTHONPATH=. ../txr1101-runtime/bin/python -m unittest discover -s tests -q`
  — 2,927 passed, 23 skipped, 92.805 seconds.
- Visual review used the real completion markup and styles with fictional
  delivery data. Desktop and 390×844 mobile views show the separate disclosure
  notice ahead of next steps, with readable wrapping and no overflow.
- `git diff --check` passed. No production/API/database reads or writes,
  customer messages, signing requests, uploads, or deployment occurred.

## Release boundary

Production baseline is `3ed1ad5c11ff44294df160d0968dee117212344e`. This change
is implemented, locally tested and visually reviewed; it is not deployed or
production-verified. Automatic Git deployments remain disabled. Do not deploy
until the full release candidate verification and Vercel headroom/cost check
pass.
