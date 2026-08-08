# Authenticated release QA

This is the release-gate run for brokerage-admin privacy and restricted Texas
REALTORS® previews. It uses an existing authenticated Supabase access token,
creates private draft previews only, and never sends a SignWell document.

## Run

From the repository root:

```bash
HOF_ACCESS_TOKEN="YOUR_EXISTING_TOKEN" \
PYTHONPATH=/private/tmp/homeofferflow_test_deps:/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python \
/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
scripts/run_authenticated_release_qa.py \
  --output-dir /tmp/homeofferflow-auth-qa
```

Do not paste the token into chat or commit it. The command writes one summary
JSON file plus a private preview and metadata-only report for each supported
form/client-count combination.

## Automated acceptance

The summary must show:

- `ok: true`
- brokerage slug `ondemand`
- brokerage privacy flags all `false` for buyer details, property details,
  offer terms, and document contents
- `signing_sent: false`
- previews for TXR-1501, TXR-1506, TXR-1507, and TXR-1508
- the form-specific signer plan preserved in each report

After the bundle finishes, run the offline validator before visual review:

```bash
PYTHONPATH=. \\
python scripts/validate_authenticated_release_qa.py \\
  /tmp/homeofferflow-auth-qa/authenticated-release-qa-summary.json
```

The validator checks all eight form/client-count combinations, confirms that
brokerage privacy flags remain false, confirms `signing_sent: false`, verifies
each preview/report exists, and rejects sensitive transaction data in the
metadata reports. It does not contact the application or create any side
effect.

Render each private preview into reviewable page images with the repository
helper:

```bash
/Users/andrewchristian/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
scripts/render_qa_pdf.py \
  /tmp/homeofferflow-auth-qa/txr-1507-1-client-private-preview.pdf \
  /tmp/homeofferflow-auth-qa/txr-1507-1-rendered
```

The helper writes `page-01.png`-style images and a metadata-only
`render-manifest.json`. It never signs or sends anything; the manifest keeps
the visual-review requirement explicit.

## Visual review

Render every generated PDF and inspect every applicable visible blank,
checkbox, initial, signature line, and date line. Record the result by form and
client count. At minimum confirm:

1. The correct private source revision is used.
2. Client/consumer and associate/broker signer roles match the report.
3. No client names, addresses, compensation, or source secrets appear in the
   metadata-only report.
4. No SignWell email or signing URL was created by this QA run.
5. Any clipping, overlap, wrong checkbox, wrong signer, or missing date is a
   failure; do not activate the form until corrected and re-rendered.

Completed-signature QA is a separate gate. It requires an explicitly approved
test transaction and a rendered, completed packet; these private previews are
not completed-signature evidence.

## Evidence to retain

Keep the summary JSON, each metadata-only report, rendered page images, and a
short reviewer note identifying the reviewed form, client count, date, and
pass/fail result. Do not retain access tokens or unnecessary client data.
