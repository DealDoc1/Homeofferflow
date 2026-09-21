#!/usr/bin/env python3
"""Fail closed before an intentional Vercel production deployment.

The release process intentionally stops after 100 deployments in a rolling
24-hour window. This conservative safety threshold remains in place across
plan changes so a misconfigured release cannot create a burst of deployments.

The same check also reserves part of the Pro monthly infrastructure credit.
That prevents a production build from starting when current-cycle usage is
already too close to on-demand billing.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import subprocess
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


# The separate public-function bundle guard is enforced by the bundle tests.
# It is independent of this deployment-frequency threshold.
DEFAULT_LIMIT = 100
DEFAULT_WINDOW_SECONDS = 24 * 60 * 60
DEFAULT_MONTHLY_CREDIT = 20.0
DEFAULT_CREDIT_RESERVE = 3.0
DEFAULT_BILLING_CYCLE_DAY = 22
DEFAULT_TEAM_SLUG = "dealdoc1s-projects"
VERCEL_BILLING_TIMEZONE = ZoneInfo("America/Los_Angeles")
UTC = timezone.utc

# These are fixed plan or add-on charges, not managed-infrastructure usage paid
# from the Pro monthly infrastructure credit.
NON_CREDIT_SERVICES = {
    "Pro",
    "Additional Team Seats",
    "Observability Plus",
    "Speed Insights Plus",
}


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


def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    index = year * 12 + month - 1 + offset
    return divmod(index, 12)[0], divmod(index, 12)[1] + 1


def _billing_cycle_dates(
    *, now: datetime, billing_cycle_day: int
) -> tuple[str, str]:
    if not 1 <= billing_cycle_day <= 28:
        raise ValueError("billing cycle day must be between 1 and 28")

    local_date = now.astimezone(VERCEL_BILLING_TIMEZONE).date()
    if local_date.day >= billing_cycle_day:
        start_year, start_month = local_date.year, local_date.month
    else:
        start_year, start_month = _shift_month(
            local_date.year, local_date.month, -1
        )
    end_year, end_month = _shift_month(start_year, start_month, 1)
    start = local_date.replace(
        year=start_year, month=start_month, day=billing_cycle_day
    )
    next_start = local_date.replace(
        year=end_year, month=end_month, day=billing_cycle_day
    )
    end = next_start - timedelta(days=1)
    return start.isoformat(), end.isoformat()


def fetch_billing_usage(
    *, token: str, team_slug: str, cycle_start: str, cycle_end: str
) -> dict:
    env = os.environ.copy()
    env["VERCEL_TOKEN"] = token
    env["VERCEL_NO_UPDATE_NOTIFIER"] = "1"
    result = subprocess.run(
        [
            "vercel",
            "usage",
            "--from",
            cycle_start,
            "--to",
            cycle_end,
            "--format",
            "json",
            "--scope",
            team_slug,
            "--non-interactive",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise ValueError("Vercel usage response was not a JSON object")
    return payload


def _infrastructure_cost(payload: dict) -> float:
    services = payload.get("services")
    if not isinstance(services, list):
        raise ValueError("Vercel usage response did not contain a services list")

    total = 0.0
    for service in services:
        if not isinstance(service, dict):
            raise ValueError("Vercel usage response contained an invalid service")
        name = service.get("name")
        cost = service.get("effectiveCost")
        if not isinstance(name, str) or not isinstance(cost, (int, float)):
            raise ValueError("Vercel usage service was missing a numeric cost")
        if name not in NON_CREDIT_SERVICES:
            total += float(cost)
    return total


def _has_safe_credit_headroom(
    *, infrastructure_cost: float, monthly_credit: float, reserve: float
) -> bool:
    if monthly_credit <= 0 or reserve < 0 or reserve >= monthly_credit:
        raise ValueError("credit and reserve values are invalid")
    return infrastructure_cost < monthly_credit - reserve


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", default="prj_LupoeEEcWigvtw6CII2bL46l0RB3")
    parser.add_argument("--team-id", default="team_BZUBDsoLMwlnaXtIES35YT4S")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--window-seconds", type=int, default=DEFAULT_WINDOW_SECONDS)
    parser.add_argument("--team-slug", default=DEFAULT_TEAM_SLUG)
    parser.add_argument(
        "--monthly-credit", type=float, default=DEFAULT_MONTHLY_CREDIT
    )
    parser.add_argument("--credit-reserve", type=float, default=DEFAULT_CREDIT_RESERVE)
    parser.add_argument(
        "--billing-cycle-day", type=int, default=DEFAULT_BILLING_CYCLE_DAY
    )
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
        f"Vercel deployment safety window: {count} deployment(s) in the last "
        f"{args.window_seconds // 3600} hour(s); limit {args.limit}."
    )
    if count >= args.limit:
        print(
            "Vercel capacity check blocked: wait for the rolling window to clear "
            "before deploying.",
            file=sys.stderr,
        )
        return 1

    try:
        cycle_start, cycle_end = _billing_cycle_dates(
            now=datetime.now(UTC), billing_cycle_day=args.billing_cycle_day
        )
        usage = fetch_billing_usage(
            token=token,
            team_slug=args.team_slug,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
        )
        infrastructure_cost = _infrastructure_cost(usage)
        safe = _has_safe_credit_headroom(
            infrastructure_cost=infrastructure_cost,
            monthly_credit=args.monthly_credit,
            reserve=args.credit_reserve,
        )
    except Exception as exc:  # fail closed if billing state cannot be read
        print(f"Vercel spend check blocked: {exc}", file=sys.stderr)
        return 2

    available = max(args.monthly_credit - infrastructure_cost, 0.0)
    print(
        "Vercel infrastructure credit safety: "
        f"${infrastructure_cost:.2f} used in {cycle_start} through {cycle_end}; "
        f"${available:.2f} unconsumed; ${args.credit_reserve:.2f} reserved."
    )
    if not safe:
        print(
            "Vercel spend check blocked: wait for the billing cycle to reset or "
            "reduce usage before deploying.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
