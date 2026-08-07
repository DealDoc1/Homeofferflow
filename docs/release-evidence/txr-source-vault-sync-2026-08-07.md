# Private source-vault sync evidence — 2026-08-07

## Scope

This record confirms that the privately supplied Texas REALTORS® and TREC
source forms used by the restricted-form foundation are present in the
OnDemand Realty brokerage source vault and match the authorized local source
PDFs by exact SHA-256. Source approval does not authorize generation, signing,
or release of any form.

## Verified records

| Form | Revision | Filename | Source-vault status | Authorization | SHA-256 match |
|---|---|---|---|---|---|
| TXR-1501 | 2026-06-15 | TXR1501.pdf | approved | attested | pass |
| TXR-1506 | 2026-06-15 | TXR1506.pdf | approved | attested | pass |
| TXR-1507 | 2026-06-15 | TXR1507.pdf | approved | attested | pass |
| TXR-1508 | 2026-02-25 | TXR1508.pdf | approved | attested | pass |
| TREC-55-1 | 05-04-2026 | seller_disclosure_notice_55-1.pdf | approved | attested | pass |
| TREC-61-0 | 05-04-2026 | seller_water_disclosure_61-0.pdf | approved | attested | pass |

The records are scoped to the OnDemand Realty brokerage source vault. The
source PDFs remain private and are not exposed to ordinary agent browser
downloads.

## Evidence basis

- Live Supabase query of `public.hof_brokerage_form_sources` on 2026-08-07.
- Live Storage verification confirmed both TREC seller PDFs under the
  brokerage-scoped private folder.
- Local SHA-256 verification against the private authorized source directory.
- The TREC-55-1 and TREC-61-0 source PDFs were uploaded only to the private
  source vault; no source was sent to SignWell.

## Gate status

The source-identity and authorization gate is complete for all six records.
The remaining gates are document-specific authenticated preview QA, signer-plan
confirmation, controlled completed-signature visual QA, and release-authority
approval. Until those gates pass, restricted forms remain preview-only and no
seller disclosure or representation form is exposed as a signing workflow.
