#!/usr/bin/env python3
"""Capture a privacy-limited Stripe lifecycle checkpoint from an isolated QA DB.

This intentionally records aggregate/status fields only. It never writes event
payloads, customer identifiers, emails, or subscription identifiers to the
snapshot. The isolation checks mirror the webhook's test-event guard so a
snapshot cannot accidentally be collected from production.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def _normalise_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _assert_isolated_environment() -> str:
    runtime_url = _normalise_url(os.environ.get("SUPABASE_URL", ""))
    test_url = _normalise_url(os.environ.get("STRIPE_WEBHOOK_TEST_SUPABASE_URL", ""))
    production_url = _normalise_url(os.environ.get("SUPABASE_PRODUCTION_URL", ""))
    vercel_environment = str(os.environ.get("VERCEL_ENV", "")).strip().lower()
    if not runtime_url or runtime_url != test_url:
        raise RuntimeError("SUPABASE_URL must equal STRIPE_WEBHOOK_TEST_SUPABASE_URL.")
    if not production_url or runtime_url == production_url:
        raise RuntimeError("The snapshot database must differ from SUPABASE_PRODUCTION_URL.")
    if vercel_environment not in {"preview", "development", "test"}:
        raise RuntimeError("Lifecycle snapshots require a nonproduction VERCEL_ENV.")
    return runtime_url


def _get_rows(base_url: str, service_key: str, table: str, select: str, limit: int) -> list[dict]:
    query = f"select={quote(select, safe=',')}&order=updated_at.desc&limit={limit}"
    request = Request(
        f"{base_url}/rest/v1/{table}?{query}",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected response from {table}.")
    return [row for row in payload if isinstance(row, dict)]


def _count_by(rows: list[dict], field: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        value = str(row.get(field) or "unknown")
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def build_snapshot(checkpoint: str, subscriptions: list[dict], members: list[dict], events: list[dict]) -> dict:
    """Return only fields safe for a QA evidence artifact."""
    return {
        "checkpoint": checkpoint,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "privacy": "aggregate lifecycle fields only; no customer, email, or Stripe identifiers",
        "subscriptions": {
            "count": len(subscriptions),
            "status_counts": _count_by(subscriptions, "status"),
            "cancel_at_period_end_count": sum(1 for row in subscriptions if row.get("cancel_at_period_end")),
            "trialing_periods": [
                {"trial_ends_at": row.get("trial_ends_at"), "updated_at": row.get("updated_at")}
                for row in subscriptions
                if row.get("status") == "trialing"
            ],
            "cancellation_periods": [
                {"cancel_at": row.get("cancel_at"), "updated_at": row.get("updated_at")}
                for row in subscriptions
                if row.get("cancel_at_period_end")
            ],
        },
        "brokerage_memberships": {
            "count": len(members),
            "status_counts": _count_by(members, "status"),
            "suspension_reason_counts": _count_by(members, "suspension_reason"),
        },
        "webhook_ledger": {
            "count": len(events),
            "event_type_counts": _count_by(events, "event_type"),
            "processing_state_counts": _count_by(events, "processing_state"),
            "livemode_counts": _count_by(
                [{"livemode": "true" if row.get("livemode") else "false"} for row in events],
                "livemode",
            ),
            "latest_received_at": max((row.get("received_at") for row in events if row.get("received_at")), default=None),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="Human-readable isolated QA checkpoint label.")
    parser.add_argument("--output", type=Path, required=True, help="JSON file to write.")
    args = parser.parse_args(argv)

    try:
        base_url = _assert_isolated_environment()
        service_key = str(os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()
        if not service_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for server-side QA capture.")
        subscriptions = _get_rows(
            base_url,
            service_key,
            "hof_subscriptions",
            "status,current_period_start,current_period_end,trial_ends_at,cancel_at_period_end,cancel_at,updated_at",
            100,
        )
        members = _get_rows(
            base_url,
            service_key,
            "hof_brokerage_members",
            "status,suspension_reason,updated_at",
            100,
        )
        events = _get_rows(
            base_url,
            service_key,
            "hof_stripe_webhook_events",
            "event_type,livemode,processing_state,received_at,processed_at,updated_at",
            200,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(build_snapshot(args.checkpoint, subscriptions, members, events), indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote isolated Stripe lifecycle snapshot to {args.output}")
        return 0
    except Exception as exc:
        print(f"Snapshot capture failed closed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
