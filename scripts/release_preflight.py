#!/usr/bin/env python3
"""Fail closed when a HomeOfferFlow packet/form release lacks required evidence.

This is intentionally a lightweight, local preflight check.  It does not
replace human legal review or rendered-PDF QA; it makes their absence visible
before a production deployment is requested.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_EVIDENCE = (
    "approved source",
    "authorization",
    "signing plan",
    "rendered signed-pdf qa",
    "regression",
    "release authority",
)


def _git_changed_files(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _git_commit_author_email() -> str:
    """Return the author email Vercel will evaluate for the deployment commit."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ae"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().lower()


def _is_packet_or_form_change(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return (
        normalized.endswith(".pdf")
        or normalized in {"api/fill-pdf.py", "api/fill_pdf_20_19_staging.py"}
        or normalized.startswith("api/fill_pdf_20_19_staging_release")
        or normalized in {"api/txr_1507_renderer.py"}
        or normalized.startswith("docs/txr_")
        or normalized.startswith("supabase/homeofferflow_brokerage_form_sources")
        or normalized.startswith("supabase/homeofferflow_generated_agreements_storage")
        or normalized.startswith("forms/")
    )


def _missing_evidence(evidence_text: str) -> list[str]:
    normalized = evidence_text.lower()
    missing = [item for item in REQUIRED_EVIDENCE if item not in normalized]
    placeholders = ("[fill", "[describe", "[link", "[name", "tbd")
    if any(marker in normalized for marker in placeholders):
        missing.append("completed evidence (not placeholders)")
    return missing


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check HomeOfferFlow release evidence before a production deployment."
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Git reference to compare with HEAD when --changed-file is not supplied.",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Explicit changed file; repeatable. Primarily useful in CI and tests.",
    )
    parser.add_argument(
        "--evidence-file",
        type=Path,
        help="Completed release-evidence Markdown file for a packet/form change.",
    )
    parser.add_argument(
        "--expected-deploy-author-email",
        help=(
            "Optional Vercel-team commit-author email. When supplied, block "
            "deployment if HEAD was authored by a different email."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.expected_deploy_author_email:
        expected_author = args.expected_deploy_author_email.strip().lower()
        actual_author = _git_commit_author_email()
        if actual_author != expected_author:
            print(
                "Preflight blocked: HEAD is authored by "
                f"{actual_author or '(missing)'}, but the Vercel deployment team "
                f"expects {expected_author}. Create the release commit with a Vercel-team "
                "member email before deploying.",
                file=sys.stderr,
            )
            return 2

    changed_files = args.changed_file or _git_changed_files(args.base)
    form_change = any(_is_packet_or_form_change(path) for path in changed_files)

    if not form_change:
        print("Preflight passed: no packet/form source or mapping change detected.")
        return 0

    if not args.evidence_file:
        print(
            "Preflight blocked: a packet/form change needs a completed "
            "release-evidence file. See docs/RELEASE_EVIDENCE_TEMPLATE.md.",
            file=sys.stderr,
        )
        return 2

    evidence_path = args.evidence_file.resolve()
    if not evidence_path.is_file():
        print(f"Preflight blocked: evidence file not found: {evidence_path}", file=sys.stderr)
        return 2

    missing = _missing_evidence(evidence_path.read_text(encoding="utf-8"))
    if missing:
        print(
            "Preflight blocked: evidence is incomplete: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2

    print("Preflight passed: completed packet/form release evidence is present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
