#!/usr/bin/env python3
"""Fail closed before connecting Stripe test events to HomeOfferFlow.

This reports only configuration state, never environment-variable values. It is
safe to run in a Vercel preview, development shell, or CI job before creating
or using a Stripe test-mode webhook endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
import sys


NONPRODUCTION_ENVIRONMENTS = {"preview", "development", "test"}


def _url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _enabled(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def check_environment(expected_supabase_url: str = "") -> dict:
    runtime_url = _url(os.environ.get("SUPABASE_URL", ""))
    test_url = _url(os.environ.get("STRIPE_WEBHOOK_TEST_SUPABASE_URL", ""))
    production_url = _url(os.environ.get("SUPABASE_PRODUCTION_URL", ""))
    environment = str(os.environ.get("VERCEL_ENV", "")).strip().lower()
    expected_url = _url(expected_supabase_url)
    checks = {
        "nonproduction_runtime": environment in NONPRODUCTION_ENVIRONMENTS,
        "test_events_explicitly_enabled": _enabled(
            os.environ.get("STRIPE_WEBHOOK_ALLOW_TEST_EVENTS", "")
        ),
        "environment_acknowledged": (
            bool(environment)
            and os.environ.get("STRIPE_WEBHOOK_TEST_ENVIRONMENT", "").strip().lower()
            == environment
        ),
        "runtime_matches_test_database": bool(runtime_url) and runtime_url == test_url,
        "runtime_differs_from_production": (
            bool(runtime_url) and bool(production_url) and runtime_url != production_url
        ),
        "expected_isolated_database": (
            not expected_url or (bool(runtime_url) and runtime_url == expected_url)
        ),
        "service_role_key_present": bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()),
        "stripe_test_key_present": os.environ.get("STRIPE_SECRET_KEY", "").strip().startswith("sk_test_"),
        "stripe_test_webhook_secret_present": os.environ.get(
            "STRIPE_SUBSCRIPTION_WEBHOOK_SECRET", ""
        ).strip().startswith("whsec_"),
    }
    return {
        "ok": all(checks.values()),
        "environment": environment or None,
        "expected_isolated_database_configured": bool(expected_url),
        "checks": checks,
        "privacy": "configuration booleans only; no database URLs or secret values are emitted",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected-supabase-url",
        default="",
        help="Exact isolated branch URL expected by this QA run. It is checked but not printed.",
    )
    args = parser.parse_args(argv)
    result = check_environment(args.expected_supabase_url)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
