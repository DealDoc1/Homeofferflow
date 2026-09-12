#!/usr/bin/env python3
"""Verify locally supplied TXR source identities before private intake.

The PDFs are intentionally outside the repository. This command checks only
the expected filename, page count, and revision text; it never copies,
uploads, or publishes a source. The authenticated source-owner intake remains
the only path that records authorization in HomeOfferFlow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader


EXPECTED = {
    "TXR-1501": {"filename": "TXR1501.pdf", "pages": 6, "revision": "06-15-26", "sha256": "d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd"},
    "TXR-1506": {"filename": "TXR1506.pdf", "pages": 6, "revision": "06-15-26", "sha256": "df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4"},
    "TXR-1507": {"filename": "TXR1507.pdf", "pages": 2, "revision": "06-15-26", "sha256": "ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46f"},
    "TXR-1508": {"filename": "TXR1508.pdf", "pages": 1, "revision": "02-25-26", "sha256": "b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40"},
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
        source_bytes = path.read_bytes()
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
        item.update({
            "actual_pages": pages,
            "revision_present": expected["revision"] in text,
            "actual_sha256": actual_sha256,
            "sha256_matches": actual_sha256 == expected["sha256"],
            "ok": pages == expected["pages"] and expected["revision"] in text and actual_sha256 == expected["sha256"],
        })
        if not item["ok"]:
            item["error"] = "filename, page-count, revision, or source-identity mismatch"
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
