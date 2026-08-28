#!/usr/bin/env python3
"""Migrate research bundles from schema 1.0 to 1.1 with backup and rollback."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MIGRATED_FILES = ("manifest.json", "sources.jsonl")
SEMANTIC_LEDGER = "semantic-audit.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Research bundle directory")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="Apply migration")
    group.add_argument("--rollback", help="Restore an explicit migration backup directory")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: root must be an object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{line_number}: record must be an object")
        records.append(value)
    return records


def atomic_write(path: Path, text: str) -> None:
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def serialize_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def serialize_jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)


def rollback(root: Path, backup_arg: str) -> int:
    backup_root = (root / "migration-backups").resolve()
    backup = Path(backup_arg).expanduser().resolve()
    if not backup.is_relative_to(backup_root):
        print("error: rollback backup must be inside this bundle's migration-backups", file=sys.stderr)
        return 2
    for name in MIGRATED_FILES:
        source = backup / name
        if not source.is_file():
            print(f"error: backup is missing {name}", file=sys.stderr)
            return 2
    for name in MIGRATED_FILES:
        shutil.copy2(backup / name, root / name)
    semantic_backup = backup / SEMANTIC_LEDGER
    semantic_marker = backup / ".semantic-audit-was-absent"
    if semantic_backup.is_file():
        shutil.copy2(semantic_backup, root / SEMANTIC_LEDGER)
    elif semantic_marker.is_file():
        (root / SEMANTIC_LEDGER).unlink(missing_ok=True)
    print(f"Rolled back research bundle from: {backup}")
    return 0


def main() -> int:
    args = parse_args()
    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    if args.rollback:
        return rollback(root, args.rollback)

    try:
        manifest = load_json(root / "manifest.json")
        sources = load_jsonl(root / "sources.jsonl")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    version = manifest.get("schema_version")
    if version == "1.1":
        print("Research bundle is already schema 1.1")
        return 0
    if version != "1.0":
        print(f"error: unsupported source schema {version}", file=sys.stderr)
        return 2

    migrated_sources: list[dict[str, Any]] = []
    for source in sources:
        item = dict(source)
        legacy_url = str(item.get("url", ""))
        item.setdefault("requested_url", legacy_url)
        item.setdefault("final_url", legacy_url)
        item.setdefault("mutable", True)
        item.setdefault("fingerprint_status", "unavailable")
        item.setdefault(
            "fingerprint_reason",
            "Migrated legacy source; inspected content was not preserved for hashing.",
        )
        migrated_sources.append(item)

    migrated_manifest = dict(manifest)
    migrated_manifest["schema_version"] = "1.1"
    migrated_manifest["updated_at"] = utc_now()
    migrated_manifest["provenance"] = {
        "fingerprint_policy": "when-permitted",
        "snapshot_policy": "local-only",
        "hash_algorithm": "sha256",
        "migrated_from": "1.0",
    }

    print(
        f"Migration preview: schema 1.0 -> 1.1; "
        f"{len(migrated_sources)} source records; apply={args.apply}"
    )
    if not args.apply:
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = root / "migration-backups" / f"{stamp}-schema-1.0-to-1.1"
    backup.mkdir(parents=True, exist_ok=False)
    for name in MIGRATED_FILES:
        shutil.copy2(root / name, backup / name)
    if (root / SEMANTIC_LEDGER).is_file():
        shutil.copy2(root / SEMANTIC_LEDGER, backup / SEMANTIC_LEDGER)
    else:
        (backup / ".semantic-audit-was-absent").touch()

    atomic_write(root / "manifest.json", serialize_json(migrated_manifest))
    atomic_write(root / "sources.jsonl", serialize_jsonl(migrated_sources))
    if not (root / SEMANTIC_LEDGER).exists():
        atomic_write(root / SEMANTIC_LEDGER, "")
    print(f"Migrated research bundle to schema 1.1")
    print(f"Rollback backup: {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
