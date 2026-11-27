# TXR-1101 dashboard integration on the release candidate

Continues the candidate based on production revision `d39d4d19d`, with
the draft, preview, and recipient-confirmation API already ported. The
agent dashboard and new or saved sale workspaces open the listing interview.
Prepared documents supports editing unsent drafts, private PDF preview, and
reviewing signer emails and the actual included and pending documents. An
unconfirmed seller-status answer returns to the matching question. If the
packet or contacts changed after review, the dialog offers a fresh review
before another send attempt. Shell version 195 is local.

84 focused tests passed across the interview, listing API, standalone review,
and PWA compatibility. Offline Chrome at 390px and 1280px ran the candidate
interview and real prepared-document dialog with fictional records and mocked
transport. Checked focused status field, saved-draft update, return to PDF
Preview, visible packet summary and email fields, confirmation payload, and
recovery from a stale packet. Reviewed both packet screenshots. Live Google
Places, hosted services, and actual provider invitations were outside the
offline fixture. No production change occurred.

The completed fictional SignWell PDF, full candidate regression, and
coordinated production release and cost verification remain.
