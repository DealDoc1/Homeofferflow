# Local TXR draft QA runbook

Use this only with privately authorized source PDFs. It produces unsigned local
drafts for visual inspection and does not activate a workflow.

```bash
python3 scripts/run_private_txr_draft_qa.py \
  "/private/path/to/HomeOfferFlow" \
  "/private/path/to/txr-draft-output"
```

The source directory must contain `TXR1501.pdf`, `TXR1506.pdf`, `TXR1507.pdf`,
and `TXR1508.pdf`. The command verifies the expected page counts and writes
`*_draft.pdf` files only to the chosen local output directory.

After generation, render every page with Poppler and visually inspect fields,
checkboxes, printed names, and spacing. This is draft evidence only. Before a
restricted form can be exposed or sent through SignWell, separately complete:

1. private source-vault upload and source-owner attestation;
2. form-specific signer-plan approval;
3. staging SignWell packet creation;
4. page-by-page completed-signature QA; and
5. release-authority approval plus regression testing.

The command intentionally has no upload, database-write, authorization, or
SignWell-send operation.
