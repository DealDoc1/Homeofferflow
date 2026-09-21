#!/usr/bin/env python3
"""Build a compact, repository-backed handoff for one HomeOfferFlow batch."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


MAX_CHANGED_PATHS = 20
MAX_RECENT_COMMITS = 8
MAX_LINE_LENGTH = 240
MAX_CONTRACT_LENGTH = 500


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _bounded_lines(value: str, limit: int) -> tuple[list[str], int]:
    lines = [line[:MAX_LINE_LENGTH] for line in value.splitlines() if line.strip()]
    return lines[:limit], max(0, len(lines) - limit)


def _contract_value(value: str) -> str:
    compact = " ".join(value.split()).strip()
    if not compact:
        raise ValueError("Batch-contract values cannot be empty.")
    if len(compact) > MAX_CONTRACT_LENGTH:
        raise ValueError(
            f"Batch-contract values must be {MAX_CONTRACT_LENGTH} characters or fewer."
        )
    return compact


def _bullet_lines(lines: list[str], omitted: int, empty: str) -> list[str]:
    output = [f"- `{line}`" for line in lines] or [f"- {empty}"]
    if omitted:
        output.append(f"- …and {omitted} more (inspect the repository if relevant).")
    return output


def build_handoff(
    *,
    root: Path,
    outcome: str,
    scope: str,
    production_revision: str,
    cost_constraint: str,
    evidence: str,
) -> str:
    branch = _git(root, "branch", "--show-current") or "detached HEAD"
    head = _git(root, "rev-parse", "--short=12", "HEAD")
    changed, changed_omitted = _bounded_lines(
        _git(root, "status", "--short"), MAX_CHANGED_PATHS
    )
    commits, commits_omitted = _bounded_lines(
        _git(root, "log", f"-{MAX_RECENT_COMMITS}", "--pretty=format:%h %s"),
        MAX_RECENT_COMMITS,
    )

    lines = [
        "# HomeOfferFlow lean task handoff",
        "",
        "## Batch contract",
        "",
        f"- Intended user outcome: {_contract_value(outcome)}",
        f"- Exact scope: {_contract_value(scope)}",
        f"- Authoritative production revision: {_contract_value(production_revision)}",
        f"- Cost/release constraint: {_contract_value(cost_constraint)}",
        f"- Completion evidence required: {_contract_value(evidence)}",
        "",
        "## Repository state",
        "",
        f"- Branch: `{branch}`",
        f"- HEAD: `{head}`",
        "- Working tree:",
        *_bullet_lines(changed, changed_omitted, "clean"),
        "",
        "## Recent commits",
        "",
        *_bullet_lines(commits, commits_omitted, "no commits found"),
        "",
        "## Operating rules",
        "",
        "- Inspect current files and external state before relying on this handoff.",
        "- Use focused tests during the batch and one full regression for the release candidate.",
        "- Distinguish local implementation, local testing, visual QA, deployment, and production verification.",
        "- Keep automatic Git deployments disabled and use one intentional production release.",
        "- Preserve unrelated user changes; do not expose credentials or private customer data.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a concise HomeOfferFlow task handoff from live Git state."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--production-revision", required=True)
    parser.add_argument("--cost-constraint", required=True)
    parser.add_argument("--evidence", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(
        build_handoff(
            root=args.root.resolve(),
            outcome=args.outcome,
            scope=args.scope,
            production_revision=args.production_revision,
            cost_constraint=args.cost_constraint,
            evidence=args.evidence,
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
