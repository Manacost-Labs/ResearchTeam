#!/usr/bin/env python3
"""Tests for deterministic research operations."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "scripts/research_ops.py"
RUN = ROOT.parent / "evaluation/benchmark/runs/BENCH-001"


class ResearchOpsTest(unittest.TestCase):
    def test_resume_reports_research_identity(self) -> None:
        result = subprocess.run(
            [sys.executable, str(OPS), "resume", str(RUN)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("research_id", result.stdout)

    def test_export_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            one, two = Path(temp) / "one.zip", Path(temp) / "two.zip"
            for output in (one, two):
                result = subprocess.run(
                    [sys.executable, str(OPS), "export", str(RUN), str(output)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                hashlib.sha256(one.read_bytes()).hexdigest(),
                hashlib.sha256(two.read_bytes()).hexdigest(),
            )


if __name__ == "__main__":
    unittest.main()
