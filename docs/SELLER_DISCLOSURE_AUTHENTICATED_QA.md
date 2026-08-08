# Seller disclosure authenticated QA

This runbook covers the private, unsigned seller-disclosure QA gate for
TREC-55-1 with the optional TREC-61-0 water-rights form. It requires an
existing authenticated Supabase access token and never creates a SignWell
document.

## Run

```bash
HOF_ACCESS_TOKEN="YOUR_EXISTING_TOKEN" \
PYTHONPATH=. \
python scripts/run_authenticated_seller_qa.py \
  --output-dir /tmp/homeofferflow-seller-qa
```

Do not paste the token into chat or commit it. The command writes one private
preview and metadata-only report for one seller and one for two sellers, plus
`authenticated-seller-qa-summary.json`.

## Validate

```bash
PYTHONPATH=. python scripts/validate_authenticated_seller_qa.py \
  /tmp/homeofferflow-seller-qa/authenticated-seller-qa-summary.json
```

The validator requires both seller counts, TREC-55-1 as the disclosure source,
TREC-61-0 as the attached water source, `seller_review_only: true`, existing
PDF previews, and `signing_sent: false`.

## Visual and release gate

Render every page of both previews and inspect each applicable response field,
checkbox, seller review area, receipt/acknowledgment area, and page transition.
Then complete a controlled signed test with the approved seller recipients and
visually inspect the completed PDF. Neither step is satisfied by this unsigned
bundle alone. Seller disclosure generation and signing remain disabled until
the completed-signature review and HomeOfferFlow release-authority approval are
recorded.
