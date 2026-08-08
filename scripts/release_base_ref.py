#!/usr/bin/env python3
"""Resolve the last production release commit for push-triggered preflight.

The production workflow may be triggered by an explicit ``[deploy-production]``
marker commit.  Comparing that marker only with ``HEAD^`` is unsafe: an empty
marker commit could hide packet or legal-form changes from earlier commits.
This helper finds the most recent *prior* production marker in the checked-out
history and fails closed when none exists.
"""

from __future__ import annotations

import subprocess
import sys


MARKER = "[deploy-production]"


def resolve_base_ref() -> str:
    result = subprocess.run(
        ["git", "log", "--format=%H%x00%s", "HEAD^"],
        check=True,
        capture_output=True,
        text=True,
    )
    for row in result.stdout.splitlines():
        sha, _, subject = row.partition("\x00")
        if MARKER in subject:
            return sha
    raise RuntimeError(
        "No prior [deploy-production] commit was found; provide an explicit "
        "workflow_dispatch base_ref before deploying."
    )


if __name__ == "__main__":
    try:
        print(resolve_base_ref())
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"Production release base resolution blocked: {exc}", file=sys.stderr)
        raise SystemExit(2)
