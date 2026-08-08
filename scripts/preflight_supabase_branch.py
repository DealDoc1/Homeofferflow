#!/usr/bin/env python3
"""Fail-closed preflight for an isolated Supabase branch attempt.

This check is intentionally local and read-only. It prevents an operator from
incurring branch charges when the repository cannot provide a complete,
ordered Supabase migration chain and configuration. It does not connect to
Supabase or create/delete a branch.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MIGRATION_NAME = re.compile(r"^(\d{14})_[a-z0-9][a-z0-9_-]*\.sql$")
PROJECT_ID = re.compile(r'^\s*project_id\s*=\s*["\']([^"\']+)["\']\s*$', re.MULTILINE)


def inspect_repository(root: Path) -> dict:
    supabase_dir = root / "supabase"
    config_path = supabase_dir / "config.toml"
    migrations_dir = supabase_dir / "migrations"
    errors: list[str] = []

    if not config_path.is_file():
        errors.append("supabase/config.toml is missing")
    else:
        config_text = config_path.read_text(encoding="utf-8")
        if not PROJECT_ID.search(config_text):
            errors.append("supabase/config.toml must declare a non-empty project_id")

    migration_files = sorted(migrations_dir.glob("*.sql")) if migrations_dir.is_dir() else []
    if not migrations_dir.is_dir():
        errors.append("supabase/migrations directory is missing")
    elif not migration_files:
        errors.append("supabase/migrations contains no SQL migrations")

    versions: list[str] = []
    invalid_names: list[str] = []
    for path in migration_files:
        match = MIGRATION_NAME.match(path.name)
        if not match:
            invalid_names.append(path.name)
        else:
            versions.append(match.group(1))
            if not path.read_text(encoding="utf-8").strip():
                errors.append(f"migration file is empty: {path.name}")

    if invalid_names:
        errors.append(
            "migration filenames must use a 14-digit version prefix: "
            + ", ".join(invalid_names)
        )
    if len(versions) != len(set(versions)):
        errors.append("migration version prefixes must be unique")

    return {
        "ok": not errors,
        "root": str(root),
        "config": str(config_path),
        "migrationCount": len(migration_files),
        "migrationVersions": versions,
        "errors": errors,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    report = inspect_repository(args.root.expanduser().resolve())
    print(json.dumps(report, indent=2))
    if report["ok"]:
        return 0
    print("Supabase branch preflight blocked: " + "; ".join(report["errors"]), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
