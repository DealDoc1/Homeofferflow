# Golden packet rendered-PDF regression

`scripts/check_golden_packet_rendering.py` renders the eleven supported golden
packets at 96 DPI and compares every page's pixel fingerprint, page count, and
SignWell field IDs to the committed baseline manifest.

The baseline is an approval artifact. Update it only after visually reviewing
the rendered pages and confirming that every intended change is correct.

```text
PYTHONPATH=/private/tmp/homeofferflow_test_deps \
/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
scripts/check_golden_packet_rendering.py
```

For an intentional, visually approved change:

```text
... scripts/check_golden_packet_rendering.py --write-baseline
```

This catches unexpected rendering changes. It does not replace completed
SignWell packet review, which remains mandatory for coordinate or signer-plan
changes.
