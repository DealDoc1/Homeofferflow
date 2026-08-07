#!/usr/bin/env python3
"""Build a deterministic manifest for the production Vercel file bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXCLUDED_PREFIXES = ("docs/", "tests/", "scripts/", "supabase/")
EXCLUDED_FILES = {"api/fill_pdf_20_19_staging.py"}


def production_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if (
            relative.startswith((".git/", ".vercel/", ".github/"))
            or "/__pycache__/" in f"/{relative}/"
            or path.name.startswith(".env")
        ):
            continue
        if relative.startswith(EXCLUDED_PREFIXES) or relative in EXCLUDED_FILES:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_manifest(root: Path) -> dict:
    entries = []
    for path in production_files(root):
        data = path.read_bytes()
        entries.append(
            {
                "file": path.relative_to(root).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return {
        "format": "homeofferflow-vercel-production-manifest-v1",
        "excluded": {
            "prefixes": list(EXCLUDED_PREFIXES),
            "files": sorted(EXCLUDED_FILES),
        },
        "file_count": len(entries),
        "total_bytes": sum(item["bytes"] for item in entries),
        "files": entries,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = build_manifest(args.root.expanduser().resolve())
    args.output.expanduser().write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("file_count", "total_bytes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
