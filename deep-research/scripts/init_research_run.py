#!/usr/bin/env python3
"""Initialize a persistent deep-research run without external dependencies."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


LEDGERS = (
    "queries.jsonl",
    "sources.jsonl",
    "evidence.jsonl",
    "claims.jsonl",
    "community.jsonl",
    "contradictions.jsonl",
    "checkpoints.jsonl",
    "semantic-audit.jsonl",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="New or empty research-run directory")
    parser.add_argument("--question", required=True, help="Main research question")
    parser.add_argument(
        "--depth", choices=("quick", "deep", "exhaustive"), default="deep"
    )
    parser.add_argument("--domain", action="append", default=[], dest="domains")
    parser.add_argument("--modifier", action="append", default=[], dest="modifiers")
    parser.add_argument("--as-of", help="Research as-of date in YYYY-MM-DD")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.directory).expanduser().resolve()
    question = args.question.strip()
    if not question:
        print("error: --question must not be empty", file=sys.stderr)
        return 2

    if target.exists() and not target.is_dir():
        print(f"error: target is not a directory: {target}", file=sys.stderr)
        return 2
    if target.exists() and any(target.iterdir()):
        print(f"error: refusing to overwrite non-empty directory: {target}", file=sys.stderr)
        return 2

    now = utc_now()
    as_of = args.as_of or now.date().isoformat()
    try:
        datetime.strptime(as_of, "%Y-%m-%d")
    except ValueError:
        print("error: --as-of must use YYYY-MM-DD", file=sys.stderr)
        return 2

    target.mkdir(parents=True, exist_ok=True)
    research_id = f"RES-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8].upper()}"
    timestamp = now.isoformat().replace("+00:00", "Z")

    manifest = {
        "schema_version": "1.1",
        "research_id": research_id,
        "main_question": question,
        "created_at": timestamp,
        "updated_at": timestamp,
        "as_of": as_of,
        "depth": args.depth,
        "modifiers": list(dict.fromkeys(args.modifiers)),
        "domain_adapters": list(dict.fromkeys(args.domains)),
        "status": "planned",
        "current_context": {},
        "prior_research_ids": [],
        "provenance": {
            "fingerprint_policy": "when-permitted",
            "snapshot_policy": "local-only",
            "hash_algorithm": "sha256"
        },
    }
    write_json(target / "manifest.json", manifest)
    for name in LEDGERS:
        (target / name).touch(exist_ok=False)

    write_json(
        target / "audit.json",
        {
            "audit_status": "not_run",
            "critical_issues": [],
            "warnings": [],
            "claims_to_rewrite": [],
            "claims_to_remove": [],
            "additional_search_required": [],
        },
    )
    (target / "report.md").write_text(
        f"# Research Report\n\nResearch ID: `{research_id}`\n\n"
        "<!-- not-yet-synthesized -->\n",
        encoding="utf-8",
    )
    (target / "handoff.md").write_text(
        f"# Research Handoff\n\nResearch ID: `{research_id}`\n\n"
        "<!-- not-yet-audited -->\n",
        encoding="utf-8",
    )

    print(f"Initialized research run: {target}")
    print(f"Research ID: {research_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
