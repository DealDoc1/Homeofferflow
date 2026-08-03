#!/usr/bin/env python3
"""Verify locally supplied TXR source identities before private intake.

The PDFs are intentionally outside the repository. This command checks only
the expected filename, page count, and revision text; it never copies,
uploads, or publishes a source. The authenticated source-owner intake remains
the only path that records authorization in HomeOfferFlow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader


EXPECTED = {
    "TXR-1501": {"filename": "TXR1501.pdf", "pages": 6, "revision": "06-15-26"},
    "TXR-1506": {"filename": "TXR1506.pdf", "pages": 6, "revision": "06-15-26"},
    "TXR-1507": {"filename": "TXR1507.pdf", "pages": 2, "revision": "06-15-26"},
    "TXR-1508": {"filename": "TXR1508.pdf", "pages": 1, "revision": "02-25-26"},
}


def verify(directory: Path):
    results = []
    for form_code, expected in EXPECTED.items():
        path = directory / expected["filename"]
        item = {"form_code": form_code, "path": str(path), "expected": expected, "ok": False}
        if not path.is_file():
            item["error"] = "missing"
            results.append(item)
            continue
        pages = len(PdfReader(str(path)).pages)
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        item.update({
            "actual_pages": pages,
            "revision_present": expected["revision"] in text,
            "ok": pages == expected["pages"] and expected["revision"] in text,
        })
        if not item["ok"]:
            item["error"] = "filename, page-count, or revision mismatch"
        results.append(item)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path, help="Private directory containing the four source PDFs")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    results = verify(args.directory.expanduser())
    if args.as_json:
        print(json.dumps({"all_ok": all(item["ok"] for item in results), "sources": results}, indent=2))
    else:
        for item in results:
            print(f"{item['form_code']}: {'OK' if item['ok'] else 'FAIL'}")
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
