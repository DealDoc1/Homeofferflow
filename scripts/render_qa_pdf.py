#!/usr/bin/env python3
"""Render a private QA PDF into page images and a metadata-only manifest.

This helper is deliberately source- and signer-agnostic. It never uploads,
signs, flattens, or modifies the input PDF. The output images are the artifact
that a reviewer must inspect page by page before a restricted workflow is
activated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader


def render(pdf_path: Path, output_dir: Path, *, dpi: int = 150) -> dict:
    pdf_path = pdf_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if dpi < 72 or dpi > 600:
        raise ValueError("dpi must be between 72 and 600")
    poppler = shutil.which("pdftoppm")
    if not poppler:
        raise RuntimeError("pdftoppm is required to render QA PDFs.")
    page_count = len(PdfReader(str(pdf_path)).pages)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"
    subprocess.run(
        [poppler, "-r", str(dpi), "-png", str(pdf_path), str(prefix)],
        check=True,
        capture_output=True,
        text=True,
    )
    pages = sorted(output_dir.glob("page-*.png"))
    if len(pages) != page_count:
        raise RuntimeError(f"Expected {page_count} rendered pages, found {len(pages)}.")
    manifest = {
        "ok": True,
        "input_page_count": page_count,
        "dpi": dpi,
        "input_filename": pdf_path.name,
        "input_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        "rendered_pages": [
            {
                "page": index,
                "filename": page.name,
                "sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
            }
            for index, page in enumerate(pages, start=1)
        ],
        "signing_sent": False,
        "visual_review_required": True,
    }
    (output_dir / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(render(args.pdf, args.output_dir, dpi=args.dpi), indent=2))
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"QA PDF render failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
