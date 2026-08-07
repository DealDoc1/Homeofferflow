# TXR-1507 authenticated QA runbook

This runbook covers the private, pre-release QA gate for the TXR-1507 Short
Residential Buyer/Tenant Representation Agreement. It does not activate a
workflow or authorize a SignWell send by itself.

## Preconditions

- Use the canonical production site and an active agent session.
- The agent must attest to current authorization to use the Texas REALTORS® /
  NAR source form at point of use.
- The brokerage authorization gate and approved private source must already be
  present.
- Do not place client names, addresses, MLS numbers, or other real transaction
  data in the QA run.

## Create a private preview

From a terminal, use an existing Supabase access token. Never commit or paste
the token into a file:

```bash
HOF_ACCESS_TOKEN="YOUR_EXISTING_SUPABASE_ACCESS_TOKEN" \
python scripts/run_authenticated_txr_qa.py \
  --form TXR-1507 \
  --output-dir /tmp/txr-1507-qa \
  --clients 1
```

Run the same command with `--clients 2` for the second signer-plan scenario.

The helper also accepts `--form TXR-1501`, `--form TXR-1508`, and
`--form TXR-1506`; each uses its own approved source record and draft action.
Those forms remain separate release candidates and do not inherit TXR-1507's
release approval.

For the seller-side disclosure preview, use the same helper with
`--form TREC-55-1`. It creates a private draft using the approved TREC-55-1
source and attaches the approved TREC-61-0 water-rights source:

```bash
HOF_ACCESS_TOKEN="YOUR_EXISTING_SUPABASE_ACCESS_TOKEN" \
python scripts/run_authenticated_txr_qa.py \
  --form TREC-55-1 \
  --output-dir /tmp/trec-seller-disclosure-qa \
  --clients 2
```

In this mode `--clients` means seller count. The helper uses anonymous QA
names, downloads the private unsigned preview, and records `seller_review_only`
in the metadata report. It never creates a signature request.

The helper creates a private draft and downloads the preview PDF. It never
sends a SignWell document and writes only metadata to its JSON report.

## Visual review checklist

For each preview PDF, inspect every visible field, checkbox, printed-name
line, signature line, and date line:

- form code and source revision are the intended values;
- client names are in the correct client rows;
- market area, term start, and term end are seated in their printed blanks;
- service level and compensation are in the selected sections;
- intermediary selection is correct;
- brokerage/associate identity is in the brokerage execution area;
- the one-client and two-client signer layouts are distinct and complete;
- no source URL, hidden source metadata, or unrelated offer data appears.

Record the result without including transaction-sensitive values.

## Controlled completed-signature QA

Only after the unsigned preview passes:

1. Use the controlled SignWell test path.
2. Sign in the exact configured order for the selected signer plan.
3. Download the completed PDF.
4. Inspect every signature, initial, date, and signer-name placement on the
   rendered completed PDF.
5. Upload the completed PDF to the private QA channel for release review.

## Release gate

TXR-1507 remains blocked from production signing until all of these are
recorded:

1. approved source revision and authorization attestation;
2. individual agent authorization attestation;
3. signer-plan review;
4. unsigned rendered-PDF review;
5. completed signed-PDF visual review;
6. regression suite pass; and
7. HomeOfferFlow release-authority approval.

Source approval alone must never expose a send or signing action.
