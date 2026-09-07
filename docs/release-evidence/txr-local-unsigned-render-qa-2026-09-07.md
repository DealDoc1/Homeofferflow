# TXR local unsigned render QA - 2026-09-07

## Scope

This local-only QA run re-rendered the supplied private source PDFs for the
current review-draft workflows:

| Form | Source revision | Pages reviewed | Source SHA-256 |
| --- | --- | ---: | --- |
| TXR-1501 | 06-15-26 | 6 | `d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd` |
| TXR-1506 | 06-15-26 | 6 | `df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4` |
| TXR-1507 | 06-15-26 | 2 | `ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46f` |
| TXR-1508 | 02-25-26 | 1 | `b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40` |

The run used `scripts/run_private_txr_draft_qa.py` against the local private
source directory. It generated unsigned drafts only and performed no upload,
database write, recipient delivery, or SignWell send.

## Result

The render command passed for all four forms. Each rendered page was visually
reviewed at 144 DPI. The reviewed sample values remained legible, stayed on
their intended printed lines, and did not overlap form text or signature and
initial areas. The signer and initial lines remain blank and available for the
separate e-signature workflow.

| Draft | Pages | Draft SHA-256 |
| --- | ---: | --- |
| TXR1501_draft.pdf | 6 | `46a348567badf1bc2f8c3d4d0ba9109d9a027183fcbd3fc3fb0262e59540ad7a` |
| TXR1506_draft.pdf | 6 | `af560de578097b1f2974b8b9e12a2e83f0ccd11323493e8be686f5aaded9f390` |
| TXR1507_draft.pdf | 2 | `86fd47e4660ca192fa9a163287345d4369a2675ea8698a4ab40a1e7e92317a76` |
| TXR1508_draft.pdf | 1 | `2ed5e5bfa9b43ed6e342444fbfff496c64854c806c2ddcabd644ba59bb84de3c` |

## Limits of this evidence

This confirms local unsigned rendering only. It does not claim that a form was
sent, signed, or enabled for an executable signature workflow. Completed
signature-PDF visual QA requires a connected authenticated SignWell test
session and a reviewed completed packet for the form's defined signer plan.
