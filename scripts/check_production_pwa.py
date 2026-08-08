#!/usr/bin/env python3
"""Run a read-only smoke check against HomeOfferFlow's public PWA shell."""

from __future__ import annotations

import argparse
import json
import urllib.request
from dataclasses import dataclass


DEFAULT_ORIGIN = "https://www.homeofferflow.com"
REQUIRED_MANIFEST = {
    "display": "standalone",
    "orientation": "portrait-primary",
    "start_url": "/",
    "scope": "/",
    "lang": "en-US",
    "dir": "ltr",
    "prefer_related_applications": False,
}


@dataclass(frozen=True)
class PwaResponse:
    status: int
    content_type: str
    body: bytes


def fetch(origin: str, path: str) -> PwaResponse:
    request = urllib.request.Request(
        origin.rstrip("/") + path,
        headers={"User-Agent": "HomeOfferFlow-PWA-Smoke/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return PwaResponse(
            status=response.status,
            content_type=response.headers.get("content-type", ""),
            body=response.read(),
        )


def validate_manifest(payload: dict) -> list[str]:
    failures = []
    for key, expected in REQUIRED_MANIFEST.items():
        if payload.get(key) != expected:
            failures.append(f"manifest {key!r} expected {expected!r}, got {payload.get(key)!r}")
    icons = payload.get("icons") or []
    if not any(icon.get("src") == "/assets/homeofferflow-app-icon.svg" for icon in icons):
        failures.append("manifest is missing the HomeOfferFlow app icon")
    return failures


def validate_shell(html: str) -> list[str]:
    required = (
        'rel="manifest" href="/manifest.webmanifest"',
        "navigator.serviceWorker.register('/service-worker.js'",
    )
    return [f"home page is missing {needle!r}" for needle in required if needle not in html]


def validate_worker(worker: str) -> list[str]:
    required = (
        "event.request.mode === 'navigate'",
        "caches.match('/index.html')",
        "requestUrl.pathname.startsWith('/api/')",
    )
    return [f"service worker is missing {needle!r}" for needle in required if needle not in worker]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    args = parser.parse_args()

    failures = []
    home = fetch(args.origin, "/")
    manifest = fetch(args.origin, "/manifest.webmanifest")
    worker = fetch(args.origin, "/service-worker.js")

    if home.status != 200:
        failures.append(f"home page returned HTTP {home.status}")
    if manifest.status != 200:
        failures.append(f"manifest returned HTTP {manifest.status}")
    if worker.status != 200:
        failures.append(f"service worker returned HTTP {worker.status}")

    failures.extend(validate_shell(home.body.decode("utf-8", errors="replace")))
    failures.extend(validate_worker(worker.body.decode("utf-8", errors="replace")))
    try:
        manifest_payload = json.loads(manifest.body)
    except json.JSONDecodeError as error:
        failures.append(f"manifest is not valid JSON: {error}")
    else:
        failures.extend(validate_manifest(manifest_payload))

    if failures:
        for failure in failures:
            print(f"PWA smoke check failed: {failure}")
        return 1
    print(f"PWA smoke check passed: {args.origin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
