# Golden packet rendering verification — 2026-08-03

## Scope

The controlled all-supported-addenda packet was rendered from the current
production adapter and compared with the approved golden manifest.

## Command

```bash
XDG_CACHE_HOME=/tmp/fontcache \
FONTCONFIG_PATH=/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/poppler/etc/fonts \
PYTHONPATH=/private/tmp/homeofferflow_test_deps:/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python \
/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
scripts/check_golden_packet_rendering.py --scenario all_supported_addenda
```

## Result

`Golden packet rendering matches the approved baseline.`

No source form, field map, signer routing, or production runtime code changed
as part of this verification.

