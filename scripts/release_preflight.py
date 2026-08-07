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
        or normalized.startswith("api/txr_")
        or normalized.startswith("lib/txr_")
        or normalized.startswith("forms/")
    )


def _missing_evidence(evidence_text: str) -> list[str]:
    normalized = evidence_text.lower()
    missing = [item for item in REQUIRED_EVIDENCE if item not in normalized]
    placeholders = ("[fill", "[describe", "[link", "[name", "tbd")
    if any(marker in normalized for marker in placeholders):
        missing.append("completed evidence (not placeholders)")
    return missing


def _required_scope_marker_groups(changed_files: list[str]) -> tuple[tuple[str, ...], ...]:
    """Return per-target scope markers the evidence must identify.

    Generic evidence is not enough for a packet/form release: a completed
    lease QA packet must not authorize an unrelated TXR or purchase-packet
    change.  Keep the markers intentionally broad enough for human-written
    evidence while requiring an unmistakable connection to the changed file.
    """
    normalized = {path.replace("\\", "/").lower() for path in changed_files}
    groups: list[tuple[str, ...]] = []
    if any(
        path.endswith("api/fill_pdf_20_19_staging.py")
        or path.startswith("api/fill_pdf_20_19_staging_release")
        for path in normalized
    ):
        groups.append(("20-19", "20 19", "purchase offer"))
    if any(path.endswith("api/fill-pdf.py") for path in normalized):
        groups.append(("production offer", "purchase offer", "contract packet"))
    if any(path.endswith("20-19_0.pdf") for path in normalized):
        groups.append(("20-19", "20 19", "purchase offer"))
    if any(path.endswith("20-18_0.pdf") for path in normalized):
        groups.append(("20-18", "20 18", "purchase offer"))
    if any(path.startswith("forms/") for path in normalized):
        groups.extend(
            (Path(path).stem.replace("_", " ").replace("-", " "),)
            for path in normalized
            if path.startswith("forms/")
        )
    txr_paths = [
        path for path in normalized
        if path.startswith("api/txr_") or path.startswith("lib/txr_")
    ]
    for path in txr_paths:
        stem = Path(path).stem.replace("_", " ").replace("-", " ")
        if stem.startswith("txr "):
            groups.append((stem,))
    # A repeated route/PDF mapping should only create one evidence requirement.
    return tuple(dict.fromkeys(groups))


def _missing_scope_evidence(evidence_text: str, changed_files: list[str]) -> str | None:
    groups = _required_scope_marker_groups(changed_files)
    if not groups:
        return None
    normalized = " ".join(evidence_text.lower().replace("_", " ").replace("-", " ").split())
    missing_groups = [group for group in groups if not any(marker in normalized for marker in group)]
    if not missing_groups:
        return None
    expected = "; ".join("one of: " + ", ".join(group) for group in missing_groups)
    return "evidence does not identify every changed packet/form scope (expected " + expected + ")"


def _missing_restricted_form_evidence(evidence_text: str, changed_files: list[str]) -> list[str]:
    """Require the stronger gates for restricted TXR renderer/source changes."""
    normalized_files = {path.replace("\\", "/").lower() for path in changed_files}
    restricted_change = any(
        path.startswith("api/txr_")
        or path.startswith("lib/txr_")
        or "brokerage_form_source" in path
        or "standalone_agreement" in path
        for path in normalized_files
    )
    if not restricted_change:
        return []
    normalized = " ".join(evidence_text.lower().replace("_", " ").replace("-", " ").split())
    required_groups = (
        ("authenticated qa", "authenticated preview qa", "authenticated point of use qa"),
        ("completed signature visual qa", "completed signed pdf qa", "completed signature qa"),
        ("source vault", "approved private source", "source revision"),
        ("agent attestation", "form use attestation", "authorized agent attestation"),
    )
    return [
        "restricted TXR evidence is missing " + "/".join(group[0] for group in required_groups if not any(marker in normalized for marker in group))
    ] if any(not any(marker in normalized for marker in group) for group in required_groups) else []


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
    missing.extend(_missing_restricted_form_evidence(evidence_path.read_text(encoding="utf-8"), changed_files))
    scope_missing = _missing_scope_evidence(
        evidence_path.read_text(encoding="utf-8"),
        changed_files,
    )
    if scope_missing:
        missing.append(scope_missing)
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
