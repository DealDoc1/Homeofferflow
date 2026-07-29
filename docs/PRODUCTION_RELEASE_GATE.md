# Production release gate

Run this command before an intentional HomeOfferFlow production deployment:

```bash
PYTHONPATH=/private/tmp/homeofferflow_test_deps \
  /Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/check_production_release_gate.py
```

It verifies all of the following:

| Gate | Evidence |
| --- | --- |
| Published contract route | `api/fill-pdf.py` uses the TREC 20-19 production adapter and `20-19_0.pdf` is present. |
| Application regression | The complete Python test suite passes. |
| Packet rendering | All ten approved golden packets render without a visual-baseline mismatch. |

## Human gates that remain required

Automation cannot approve a legal-form release. Before releasing a new or
changed form workflow, verify:

1. The brokerage has privately authorized the exact current source PDF.
2. The workflow has an approved signer plan.
3. Every applicable blank, checkbox, initial, signature, and date was visually
   checked in a completed signed PDF.
4. Only the specifically proven coordinates changed; locked/pass coordinates
   stayed unchanged.

For the published TREC 20-19 buyer-offer route, do not reopen coordinate work
unless an actual regression is observed.
