#!/usr/bin/env python3
"""Fail closed before an intentional Vercel production deployment.

Vercel Hobby accounts allow 100 deployments per rolling 24-hour window. The
release workflow uses this check before building or deploying so an authorized
release cannot consume another deployment while that window is already full.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# The separate 12-function project cap is enforced by the bundle tests. It is
# not the Hobby deployment-per-day limit.
DEFAULT_LIMIT = 100
DEFAULT_WINDOW_SECONDS = 24 * 60 * 60


def _deployment_count(payload: dict, *, now_ms: int, window_ms: int) -> int:
    deployments = payload.get("deployments")
    if not isinstance(deployments, list):
        raise ValueError("Vercel response did not contain a deployments list")
    cutoff = now_ms - window_ms
    return sum(
        1
        for deployment in deployments
        if isinstance(deployment, dict)
        and isinstance(deployment.get("created"), (int, float))
        and deployment["created"] >= cutoff
    )


def fetch_deployment_count(
    *, token: str, project_id: str, team_id: str, now_ms: int, window_seconds: int
) -> int:
    query = urlencode(
        {
            "projectId": project_id,
            "teamId": team_id,
            "from": now_ms - window_seconds * 1000,
            "limit": 100,
        }
    )
    request = Request(
        f"https://api.vercel.com/v6/deployments?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed Vercel API URL
        payload = json.load(response)
    return _deployment_count(
        payload, now_ms=now_ms, window_ms=window_seconds * 1000
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", default="prj_LupoeEEcWigvtw6CII2bL46l0RB3")
    parser.add_argument("--team-id", default="team_BZUBDsoLMwlnaXtIES35YT4S")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--window-seconds", type=int, default=DEFAULT_WINDOW_SECONDS)
    args = parser.parse_args()

    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        print("Vercel capacity check blocked: VERCEL_TOKEN is not set", file=sys.stderr)
        return 2

    now_ms = int(time.time() * 1000)
    try:
        count = fetch_deployment_count(
            token=token,
            project_id=args.project_id,
            team_id=args.team_id,
            now_ms=now_ms,
            window_seconds=args.window_seconds,
        )
    except Exception as exc:  # fail closed if the account state cannot be read
        print(f"Vercel capacity check blocked: {exc}", file=sys.stderr)
        return 2

    print(
        f"Vercel Hobby deployment window: {count} deployment(s) in the last "
        f"{args.window_seconds // 3600} hour(s); limit {args.limit}."
    )
    if count >= args.limit:
        print(
            "Vercel capacity check blocked: wait for the rolling window to clear "
            "before deploying.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
