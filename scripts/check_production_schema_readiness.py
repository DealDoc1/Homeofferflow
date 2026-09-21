#!/usr/bin/env python3
"""Fail closed unless production Supabase satisfies the release schema contract."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


EXPECTED_CONTRACT = "homeofferflow-release-schema-v1"
URL_KEYS = ("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "VITE_SUPABASE_URL")
SERVICE_KEY_KEYS = (
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_SECRET_KEY",
)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def first_value(names: tuple[str, ...], values: dict[str, str]) -> str:
    for name in names:
        value = str(os.environ.get(name) or values.get(name) or "").strip()
        if value:
            return value
    return ""


def fetch_readiness(url: str, service_key: str) -> dict:
    endpoint = f"{url.rstrip('/')}/rest/v1/rpc/hof_release_schema_readiness"
    request = Request(
        endpoint,
        data=b"{}",
        method="POST",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HomeOfferFlow-production-schema-check/1",
        },
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310 - configured Supabase URL
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("readiness RPC returned a non-object response")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)

    file_values: dict[str, str] = {}
    if args.env_file:
        if not args.env_file.is_file():
            print("Production schema check blocked: environment file is missing", file=sys.stderr)
            return 2
        file_values = parse_env_file(args.env_file)

    url = first_value(URL_KEYS, file_values)
    service_key = first_value(SERVICE_KEY_KEYS, file_values)
    if not url or not service_key:
        print(
            "Production schema check blocked: Supabase URL or service credential is unavailable",
            file=sys.stderr,
        )
        return 2

    try:
        payload = fetch_readiness(url, service_key)
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Production schema check blocked: {exc}", file=sys.stderr)
        return 2

    contract = payload.get("contract")
    missing = payload.get("missing")
    if contract != EXPECTED_CONTRACT or payload.get("ready") is not True or missing != []:
        safe_missing = missing if isinstance(missing, list) else ["invalid readiness response"]
        print(
            "Production schema check blocked: required database capabilities are missing: "
            + ", ".join(str(item) for item in safe_missing),
            file=sys.stderr,
        )
        return 1

    print(f"Production Supabase schema is ready ({EXPECTED_CONTRACT}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
