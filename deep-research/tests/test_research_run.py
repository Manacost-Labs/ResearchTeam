#!/usr/bin/env python3
"""Integration tests for persistent research-run tooling."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts/init_research_run.py"
VALIDATE = ROOT / "scripts/validate_research_run.py"
MIGRATE = ROOT / "scripts/migrate_research_bundle.py"
FINGERPRINT = ROOT / "scripts/fingerprint_research_sources.py"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)
    path.write_text(text, encoding="utf-8")


class ResearchRunToolsTest(unittest.TestCase):
    def initialize(self, parent: Path) -> Path:
        run = parent / "run"
        result = subprocess.run(
            [
                sys.executable,
                str(INIT),
                str(run),
                "--question",
                "What exactly determines the current mechanic?",
                "--depth",
                "deep",
                "--domain",
                "hearthstone",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return run

    def test_initialized_run_passes_working_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self.initialize(Path(temp))
            result = subprocess.run(
                [sys.executable, str(VALIDATE), str(run), "--stage", "working"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Research bundle: PASS", result.stdout)

    def test_complete_linked_run_passes_final_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self.initialize(Path(temp))
            manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
            manifest["status"] = "complete"
            write_json(run / "manifest.json", manifest)
            write_jsonl(
                run / "queries.jsonl",
                [
                    {
                        "query_id": "QRY-0001",
                        "pass": "discovery",
                        "family": "primary",
                        "query": "fixture query",
                        "executed_at": "2026-08-28T08:00:00Z",
                        "status": "executed",
                    }
                ],
            )
            write_jsonl(
                run / "sources.jsonl",
                [
                    {
                        "source_id": "SRC-0001",
                        "title": "Inspected primary source",
                        "requested_url": "https://example.com/original",
                        "final_url": "https://example.com/original",
                        "accessed_at": "2026-08-28T08:00:00Z",
                        "access_integrity": "full",
                        "source_type": "official",
                        "lineage_id": "LIN-0001",
                        "mutable": True,
                        "fingerprint_status": "unavailable",
                        "fingerprint_reason": "Fixture has no preserved source content.",
                    }
                ],
            )
            write_jsonl(
                run / "evidence.jsonl",
                [
                    {
                        "evidence_id": "EVD-0001",
                        "source_id": "SRC-0001",
                        "claim_ids": ["CLM-0001"],
                        "relationship": "supports",
                        "locator": {"section": "Rules"},
                        "evidence_type": "fact",
                        "faithful_paraphrase": "Fixture evidence for integrity testing only.",
                    }
                ],
            )
            write_jsonl(
                run / "claims.jsonl",
                [
                    {
                        "claim_id": "CLM-0001",
                        "claim": "Fixture claim for integrity testing only.",
                        "importance": "critical",
                        "status": "supported",
                        "confidence": "HIGH",
                        "supporting_evidence_ids": ["EVD-0001"],
                        "challenging_evidence_ids": [],
                    }
                ],
            )
            write_jsonl(
                run / "semantic-audit.jsonl",
                [
                    {
                        "semantic_audit_id": "SEM-0001",
                        "claim_id": "CLM-0001",
                        "evidence_id": "EVD-0001",
                        "source_id": "SRC-0001",
                        "semantic_support": "exact",
                        "scope_match": True,
                        "authority_match": True,
                        "freshness_match": True,
                        "evidence_type_match": True,
                        "reviewer_status": "pass",
                        "reviewer_basis": "Fixture evidence exactly supports the fixture claim.",
                        "audited_at": "2026-08-28T08:05:00Z",
                    }
                ],
            )
            write_json(
                run / "audit.json",
                {
                    "audit_status": "pass",
                    "critical_issues": [],
                    "warnings": [],
                    "claims_to_rewrite": [],
                    "claims_to_remove": [],
                    "additional_search_required": [],
                },
            )
            (run / "report.md").write_text(
                "# Research Report\n\nThis is a non-factual fixture report used only to verify "
                "that a completed bundle passes structural and referential-integrity checks.\n",
                encoding="utf-8",
            )
            (run / "handoff.md").write_text(
                "# Research Handoff\n\nFixture handoff: validator pass, audit pass, no factual delivery.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(VALIDATE), str(run), "--stage", "final"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_broken_evidence_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self.initialize(Path(temp))
            write_jsonl(
                run / "claims.jsonl",
                [
                    {
                        "claim_id": "CLM-0001",
                        "claim": "Broken fixture claim.",
                        "importance": "material",
                        "status": "supported",
                        "confidence": "HIGH",
                        "supporting_evidence_ids": ["EVD-9999"],
                        "challenging_evidence_ids": [],
                    }
                ],
            )
            result = subprocess.run(
                [sys.executable, str(VALIDATE), str(run), "--stage", "working"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown evidence EVD-9999", result.stdout)

    def test_initializer_refuses_to_overwrite_non_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run"
            run.mkdir()
            (run / "keep.txt").write_text("user data", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(INIT),
                    str(run),
                    "--question",
                    "Should not overwrite this directory",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((run / "keep.txt").read_text(encoding="utf-8"), "user data")

    def test_query_without_execution_timestamp_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self.initialize(Path(temp))
            write_jsonl(
                run / "queries.jsonl",
                [
                    {
                        "query_id": "QRY-0001",
                        "pass": "discovery",
                        "family": "primary",
                        "query": "fixture query without timestamp",
                        "status": "executed",
                    }
                ],
            )
            result = subprocess.run(
                [sys.executable, str(VALIDATE), str(run), "--stage", "working"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing executed_at", result.stdout)

    def test_schema_1_0_migration_can_be_rolled_back(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self.initialize(Path(temp))
            manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
            manifest["schema_version"] = "1.0"
            manifest.pop("provenance", None)
            write_json(run / "manifest.json", manifest)
            (run / "semantic-audit.jsonl").unlink()
            write_jsonl(
                run / "sources.jsonl",
                [
                    {
                        "source_id": "SRC-0001",
                        "title": "Legacy source",
                        "url": "https://example.com/legacy",
                        "accessed_at": "2026-08-28T08:00:00Z",
                        "access_integrity": "full",
                        "source_type": "official",
                        "lineage_id": "LIN-0001",
                    }
                ],
            )
            apply_result = subprocess.run(
                [sys.executable, str(MIGRATE), str(run), "--apply"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(apply_result.returncode, 0, apply_result.stdout + apply_result.stderr)
            migrated = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(migrated["schema_version"], "1.1")
            backup_line = next(
                line for line in apply_result.stdout.splitlines() if line.startswith("Rollback backup:")
            )
            backup = backup_line.split(":", 1)[1].strip()
            rollback_result = subprocess.run(
                [sys.executable, str(MIGRATE), str(run), "--rollback", backup],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                rollback_result.returncode, 0, rollback_result.stdout + rollback_result.stderr
            )
            restored = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(restored["schema_version"], "1.0")
            self.assertFalse((run / "semantic-audit.jsonl").exists())

    def test_snapshot_fingerprint_is_recorded_and_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run = self.initialize(Path(temp))
            snapshots = run / "snapshots"
            snapshots.mkdir()
            (snapshots / "SRC-0001.txt").write_text(
                "Preserved inspected source content.\n", encoding="utf-8"
            )
            write_jsonl(
                run / "sources.jsonl",
                [
                    {
                        "source_id": "SRC-0001",
                        "title": "Snapshot source",
                        "requested_url": "https://example.com/requested",
                        "final_url": "https://example.com/final",
                        "accessed_at": "2026-08-28T08:00:00Z",
                        "access_integrity": "full",
                        "source_type": "official",
                        "lineage_id": "LIN-0001",
                        "mutable": True,
                        "fingerprint_status": "unavailable",
                        "fingerprint_reason": "Awaiting local fingerprint pass.",
                        "snapshot_path": "snapshots/SRC-0001.txt",
                    }
                ],
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(FINGERPRINT),
                    str(run),
                    "--apply",
                    "--require-all",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            source = json.loads((run / "sources.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(source["fingerprint_status"], "verified")
            self.assertEqual(len(source["content_sha256"]), 64)
            validation = subprocess.run(
                [sys.executable, str(VALIDATE), str(run), "--stage", "working"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)


if __name__ == "__main__":
    unittest.main()
