#!/usr/bin/env python3
"""Tests for search planning, search coverage, source fetching, and the shared taxonomy."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from urllib.request import Request


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
INIT = SCRIPTS / "init_research_run.py"
PLAN = SCRIPTS / "plan_queries.py"
COVERAGE = SCRIPTS / "search_coverage.py"
FETCH = SCRIPTS / "fetch_source.py"
VALIDATE = SCRIPTS / "validate_research_run.py"
FINGERPRINT = SCRIPTS / "fingerprint_research_sources.py"
MIGRATE = SCRIPTS / "migrate_research_bundle.py"
sys.path.insert(0, str(SCRIPTS))

import fetch_source  # noqa: E402
import search_coverage  # noqa: E402
from search_support import (  # noqa: E402
    QUERY_FAMILIES,
    canonical_url,
    lineage_hint,
    next_id,
    normalize_query,
)


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args], check=False, capture_output=True, text=True
    )


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def init_bundle(target: Path, *, profile: str = "research-report", depth: str = "deep") -> None:
    result = run(
        INIT,
        str(target),
        "--question",
        "How should the first Dark Gift be used in Battlegrounds?",
        "--depth",
        depth,
        "--domain",
        "hearthstone",
        "--output-profile",
        profile,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def executed_query(query_id: str, family: str, query: str, sources: list[str]) -> dict[str, Any]:
    return {
        "query_id": query_id,
        "pass": "discovery",
        "family": family,
        "language": "en",
        "query": query,
        "executed_at": "2026-09-01T10:00:00Z",
        "status": "completed",
        "result_source_ids": sources,
    }


def source(
    source_id: str, url: str, lineage: str, *, verified: bool = False, run_dir: Path | None = None
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source_id": source_id,
        "title": f"Source {source_id}",
        "requested_url": url,
        "final_url": url,
        "accessed_at": "2026-09-01T10:05:00Z",
        "access_integrity": "full",
        "source_type": "official",
        "lineage_id": lineage,
        "mutable": True,
        "fingerprint_status": "verified" if verified else "unavailable",
    }
    if verified:
        assert run_dir is not None
        (run_dir / "snapshots").mkdir(exist_ok=True)
        payload = f"Source: {source_id}\nURL: {url}\n\nfixture text\n".encode("utf-8")
        (run_dir / "snapshots" / f"{source_id}.txt").write_bytes(payload)
        record["snapshot_path"] = f"snapshots/{source_id}.txt"
        record["content_sha256"] = hashlib.sha256(payload).hexdigest()
        record["content_bytes"] = len(payload)
        record["fingerprinted_at"] = "2026-09-01T10:06:00Z"
    else:
        record["fingerprint_reason"] = "test fixture"
    return record


class SearchSupportTest(unittest.TestCase):
    def test_canonical_url_strips_tracking_fragment_and_mobile_prefix(self) -> None:
        self.assertEqual(
            canonical_url("HTTPS://m.Example.com:443/path/?utm_source=x&b=2&a=1#frag"),
            "https://example.com/path?a=1&b=2",
        )
        self.assertEqual(
            canonical_url("https://www.reddit.com/r/hearthstone/"),
            "https://reddit.com/r/hearthstone",
        )

    def test_lineage_hint_is_stable_for_equivalent_urls(self) -> None:
        one = lineage_hint("https://example.com/a?utm_medium=social")
        two = lineage_hint("https://www.example.com/a/")
        self.assertEqual(one, two)
        self.assertTrue(one.startswith("LIN-EXAMPLE-COM-"))

    def test_normalize_query_and_next_id(self) -> None:
        self.assertEqual(normalize_query('  "Dark Gift"   Timing '), "dark gift timing")
        self.assertEqual(next_id("QRY", {"QRY-0003", "QRY-0010", "junk"}), "QRY-0011")
        self.assertEqual(next_id("SRC", set()), "SRC-0001")
        self.assertIn("counterargument", QUERY_FAMILIES)


class PlanQueriesTest(unittest.TestCase):
    def test_plan_expands_sections_languages_entities_and_dedups(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            init_bundle(run_dir, profile="editor-ready", depth="exhaustive")
            plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
            plan["deliverable_outline"] = [
                {
                    "section_id": "SEC-0001",
                    "working_title": "Dark Gift timing",
                    "reader_question": "When to press it?",
                    "readiness_condition": "x",
                    "status": "planned",
                    "coverage_note": "",
                },
                {
                    "section_id": "SEC-0002",
                    "working_title": "Excluded section",
                    "reader_question": "",
                    "readiness_condition": "x",
                    "status": "excluded",
                    "coverage_note": "out of scope",
                },
            ]
            (run_dir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
            write_jsonl(
                run_dir / "queries.jsonl",
                [executed_query("QRY-0007", "general", "Dark Gift timing explained", [])],
            )
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            manifest["current_context"] = {"patch": "36.4"}
            (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            preview = run(PLAN, str(run_dir), "--language", "en", "--language", "ru", "--entity", "Jeef")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertFalse((run_dir / "query-plan.jsonl").exists())

            applied = run(
                PLAN, str(run_dir), "--language", "en", "--language", "ru", "--entity", "Jeef", "--apply"
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            records = read_jsonl(run_dir / "query-plan.jsonl")
            self.assertTrue(records)
            queries = [record["query"] for record in records]
            self.assertNotIn("Dark Gift timing explained", queries)
            self.assertIn("Dark Gift timing patch notes 36.4", queries)
            self.assertIn("Jeef overrated", queries)
            self.assertIn("Dark Gift timing ошибки", queries)
            self.assertTrue(all(record["deliverable_section_ids"] == ["SEC-0001"] for record in records))
            self.assertTrue(all(record["status"] == "planned" for record in records))
            self.assertEqual(records[0]["query_id"], "QRY-0008")
            self.assertEqual(len(queries), len({normalize_query(query) for query in queries}))
            families = {record["family"] for record in records}
            self.assertIn("localized", families)
            self.assertIn("counterargument", families)

            rerun = run(PLAN, str(run_dir), "--language", "en", "--language", "ru", "--entity", "Jeef", "--apply")
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            self.assertEqual(len(read_jsonl(run_dir / "query-plan.jsonl")), len(records))

    def test_plan_refuses_long_topic_and_unknown_family(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            init_bundle(run_dir)
            result = run(PLAN, str(run_dir), "--topic", " ".join(["word"] * 13))
            self.assertEqual(result.returncode, 2)
            self.assertIn("--topic", result.stderr)
            result = run(PLAN, str(run_dir), "--topic", "Dark Gift", "--family", "nonsense")
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown query family", result.stderr)
            quick = run(PLAN, str(run_dir), "--topic", "Dark Gift", "--json")
            self.assertEqual(quick.returncode, 0, quick.stderr)
            families = {json.loads(line)["family"] for line in quick.stdout.splitlines()}
            self.assertEqual(families, {"general", "primary", "statistics", "experts", "reddit", "x", "youtube", "mistakes", "counterargument", "freshness"})


class SearchCoverageTest(unittest.TestCase):
    def build_bundle(self, run_dir: Path) -> None:
        """A legacy schema 1.1 bundle: free-text families are warnings, not errors."""

        init_bundle(run_dir, depth="quick")
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        manifest["schema_version"] = "1.1"
        (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        write_jsonl(
            run_dir / "queries.jsonl",
            [
                executed_query("QRY-0001", "primary", "Dark Gift official", ["SRC-0001"]),
                executed_query("QRY-0002", "freshness", "Dark Gift 36.4", ["SRC-0002"]),
                executed_query("QRY-0003", "legacy label", "Dark Gift stats", []),
            ],
        )
        write_jsonl(
            run_dir / "sources.jsonl",
            [
                source("SRC-0001", "https://hearthstone.blizzard.com/news/1", "LIN-A", verified=True, run_dir=run_dir),
                source("SRC-0002", "https://hearthstone.blizzard.com/news/2", "LIN-A"),
            ],
        )
        write_jsonl(
            run_dir / "evidence.jsonl",
            [
                {"evidence_id": "EVD-0001", "source_id": "SRC-0001", "claim_ids": ["CLM-0001", "CLM-0002"], "relationship": "supporting", "locator": "p1", "evidence_type": "fact", "faithful_paraphrase": "x"},
                {"evidence_id": "EVD-0002", "source_id": "SRC-0002", "claim_ids": ["CLM-0001"], "relationship": "supporting", "locator": "p2", "evidence_type": "fact", "faithful_paraphrase": "y"},
            ],
        )
        write_jsonl(
            run_dir / "claims.jsonl",
            [
                {"claim_id": "CLM-0001", "claim": "critical thing", "importance": "critical", "status": "supported", "confidence": "HIGH", "supporting_evidence_ids": ["EVD-0001", "EVD-0002"], "challenging_evidence_ids": []},
                {"claim_id": "CLM-0002", "claim": "material thing", "importance": "material", "status": "supported", "confidence": "MEDIUM", "supporting_evidence_ids": ["EVD-0001"], "challenging_evidence_ids": [], "challenge_search": {"query_ids": ["QRY-0002"], "result": "none_found"}},
            ],
        )

    def test_report_flags_missing_families_challenges_and_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build_bundle(run_dir)
            report = search_coverage.analyze(run_dir)
            errors = "\n".join(report["findings"]["errors"])
            warnings = "\n".join(report["findings"]["warnings"])
            self.assertIn("missing required quick query families: counterargument", errors)
            self.assertIn("CLM-0001", errors)
            self.assertNotIn("CLM-0002", errors)
            self.assertIn("share one lineage: CLM-0001", warnings)
            self.assertIn("share one host: CLM-0001", warnings)
            self.assertIn("fingerprint coverage 1/2", warnings)
            self.assertIn("no candidates.jsonl", warnings)
            self.assertEqual(report["queries"]["non_canonical_family"], ["QRY-0003"])
            self.assertEqual(report["claims"]["challenge_coverage"], 0.5)
            self.assertEqual(report["branches"]["__all__"]["families_present"], ["freshness", "primary"])

            strict = run(COVERAGE, str(run_dir), "--strict")
            self.assertEqual(strict.returncode, 1)
            self.assertIn("Search coverage: FAIL", strict.stdout)
            lenient = run(COVERAGE, str(run_dir), "--json")
            self.assertEqual(lenient.returncode, 0)
            self.assertEqual(json.loads(lenient.stdout)["depth"], "quick")

    def test_report_passes_when_families_and_challenges_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build_bundle(run_dir)
            queries = read_jsonl(run_dir / "queries.jsonl")
            queries.append(executed_query("QRY-0004", "counterargument", "why not Dark Gift", []))
            write_jsonl(run_dir / "queries.jsonl", queries)
            write_jsonl(
                run_dir / "query-plan.jsonl",
                [{"query_id": "QRY-0005", "family": "reddit", "query": "site:reddit.com Dark Gift", "status": "planned"}],
            )
            write_jsonl(
                run_dir / "candidates.jsonl",
                [
                    {"candidate_id": "CAN-0001", "query_id": "QRY-0001", "url": "https://hearthstone.blizzard.com/news/1", "decision": "opened", "source_id": "SRC-0001"},
                    {"candidate_id": "CAN-0002", "query_id": "QRY-0001", "url": "https://aggregator.example/x", "decision": "rejected", "reason": "duplicate_lineage"},
                ],
            )
            claims = read_jsonl(run_dir / "claims.jsonl")
            claims[0]["challenge_search"] = {"query_ids": ["QRY-0004"], "result": "none_found"}
            write_jsonl(run_dir / "claims.jsonl", claims)
            report = search_coverage.analyze(run_dir)
            self.assertEqual(report["findings"]["errors"], [])
            self.assertEqual(report["plan"]["unexecuted_ids"], ["QRY-0005"])
            self.assertEqual(report["candidates"]["open_rate"], 0.5)
            self.assertEqual(report["candidates"]["rejections_by_reason"], {"duplicate_lineage": 1})

            validation = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(validation.returncode, 0, validation.stdout)
            self.assertIn("non-canonical query family 'legacy label'", validation.stdout)

    def test_validator_rejects_malformed_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build_bundle(run_dir)
            write_jsonl(
                run_dir / "candidates.jsonl",
                [
                    {"candidate_id": "CAN-0001", "query_id": "QRY-9999", "url": "https://a.example", "decision": "opened", "source_id": "SRC-0009"},
                    {"candidate_id": "CAN-0001", "query_id": "QRY-0001", "url": "https://b.example", "decision": "rejected"},
                    {"candidate_id": "CAN-0003", "query_id": "QRY-0001", "url": "https://c.example", "decision": "maybe"},
                ],
            )
            validation = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(validation.returncode, 1)
            self.assertIn("unknown query QRY-9999", validation.stdout)
            self.assertIn("must reference a known source_id", validation.stdout)
            self.assertIn("duplicate ID CAN-0001", validation.stdout)
            self.assertIn("needs a canonical reason", validation.stdout)
            self.assertIn("invalid decision", validation.stdout)


HTML_FIXTURE = """<!doctype html><html><head><meta charset="utf-8"><title> Dark Gift  Developer Insight </title>
<style>body{color:red}</style><script>window.x = 1;</script></head>
<body><nav>Menu</nav><h1>Dark Gifts</h1><p>Dark Discovery costs <b>3</b> gold.</p>
<div><p>It unlocks on turn three.</p></div><noscript>enable js</noscript></body></html>"""


def fake_transport(status: int = 200, final_url: str | None = None, body: bytes | None = None, content_type: str = "text/html; charset=utf-8"):
    def transport(request: Request, timeout: float):
        assert "Cookie" not in request.headers
        assert request.get_header("User-agent", "").startswith("deep-research-fetch-source")
        return status, final_url or request.full_url, {"Content-Type": content_type}, body if body is not None else HTML_FIXTURE.encode("utf-8")

    return transport


class FetchSourceTest(unittest.TestCase):
    def test_html_to_text_drops_scripts_and_keeps_title(self) -> None:
        title, text = fetch_source.html_to_text(HTML_FIXTURE)
        self.assertEqual(title, "Dark Gift Developer Insight")
        self.assertIn("Dark Discovery costs 3 gold.", text)
        self.assertIn("It unlocks on turn three.", text)
        self.assertNotIn("window.x", text)
        self.assertNotIn("color:red", text)
        self.assertNotIn("enable js", text)

    def test_url_safety_rules(self) -> None:
        for bad in ("ftp://example.com/x", "https://user:pw@example.com/x", "http://localhost/x", "http://10.0.0.1/x", "http://[::1]/x"):
            with self.subTest(url=bad):
                with self.assertRaises(fetch_source.FetchError):
                    fetch_source.check_url(bad, allow_private=False)
        fetch_source.check_url("http://10.0.0.1/x", allow_private=True)
        fetch_source.check_url("https://hearthstone.blizzard.com/news", allow_private=False)

    def test_fetch_rejects_non_200_and_binary(self) -> None:
        with self.assertRaises(fetch_source.FetchError):
            fetch_source.fetch("https://example.com/x", transport=fake_transport(status=404))
        with self.assertRaises(fetch_source.FetchError):
            fetch_source.fetch("https://example.com/x", transport=fake_transport(content_type="application/pdf"))
        with self.assertRaises(fetch_source.FetchError):
            fetch_source.fetch("https://example.com/x", transport=fake_transport(body=b"x" * (fetch_source.MAX_RESPONSE_BYTES + 1)))

    def test_apply_records_verified_source_and_links_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            init_bundle(run_dir)
            write_jsonl(run_dir / "queries.jsonl", [executed_query("QRY-0001", "primary", "Dark Gift official", [])])
            url = "https://us.forums.blizzard.com/en/hearthstone/t/dark-gifts/163606?utm_source=x"
            preview = fetch_source.main([str(run_dir), url, "--query-id", "QRY-0001"], transport=fake_transport(final_url=url.split("?")[0]))
            self.assertEqual(preview, 0)
            self.assertEqual(read_jsonl(run_dir / "sources.jsonl"), [])

            applied = fetch_source.main(
                [str(run_dir), url, "--query-id", "QRY-0001", "--source-type", "official", "--platform", "forum", "--apply"],
                transport=fake_transport(final_url=url.split("?")[0]),
            )
            self.assertEqual(applied, 0)
            sources = read_jsonl(run_dir / "sources.jsonl")
            self.assertEqual(len(sources), 1)
            record = sources[0]
            self.assertEqual(record["source_id"], "SRC-0001")
            self.assertEqual(record["title"], "Dark Gift Developer Insight")
            self.assertEqual(record["final_url"], url.split("?")[0])
            self.assertEqual(record["canonical_url"], "https://us.forums.blizzard.com/en/hearthstone/t/dark-gifts/163606")
            self.assertEqual(record["fingerprint_status"], "verified")
            self.assertTrue(record["mutable"])
            self.assertEqual(record["platform"], "forum")
            self.assertEqual(record["found_by_query_ids"], ["QRY-0001"])
            snapshot = run_dir / record["snapshot_path"]
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), record["content_sha256"])
            self.assertEqual(snapshot.stat().st_size, record["content_bytes"])
            self.assertIn("Dark Discovery costs 3 gold.", snapshot.read_text(encoding="utf-8"))
            queries = read_jsonl(run_dir / "queries.jsonl")
            self.assertEqual(queries[0]["result_source_ids"], ["SRC-0001"])

            duplicate = fetch_source.main([str(run_dir), "https://www.us.forums.blizzard.com/en/hearthstone/t/dark-gifts/163606/", "--apply"], transport=fake_transport())
            self.assertEqual(duplicate, 1)
            self.assertEqual(len(read_jsonl(run_dir / "sources.jsonl")), 1)

            fingerprint = run(FINGERPRINT, str(run_dir))
            self.assertEqual(fingerprint.returncode, 0, fingerprint.stderr)
            self.assertIn("1 verified, 0 missing", fingerprint.stdout)
            validation = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(validation.returncode, 0, validation.stdout)

    def test_file_mode_ingests_saved_page_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            init_bundle(run_dir)
            saved = Path(temp) / "page.html"
            saved.write_text(HTML_FIXTURE, encoding="utf-8")
            result = run(FETCH, str(run_dir), "https://example.com/insight", "--file", str(saved), "--immutable", "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            record = read_jsonl(run_dir / "sources.jsonl")[0]
            self.assertFalse(record["mutable"])
            self.assertEqual(record["retrieved_by"], "fetch_source.py --file")
            self.assertNotIn("http_status", record)
            self.assertTrue(record["lineage_id"].startswith("LIN-EXAMPLE-COM-"))

            unknown_query = run(FETCH, str(run_dir), "https://example.com/other", "--file", str(saved), "--query-id", "QRY-0042", "--apply")
            self.assertEqual(unknown_query.returncode, 2)
            self.assertIn("unknown query", unknown_query.stderr)


if __name__ == "__main__":
    unittest.main()


class Schema12Test(unittest.TestCase):
    """Schema 1.2 search-integrity rules: canonical queries, excerpt anchors, challenge quota."""

    def build(self, run_dir: Path) -> None:
        init_bundle(run_dir, depth="quick")
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "1.2")
        write_jsonl(
            run_dir / "queries.jsonl",
            [
                executed_query("QRY-0001", "primary", "Dark Gift official", ["SRC-0001"]),
                {**executed_query("QRY-0002", "counterargument", "why not Dark Gift", []), "pass": "contradiction"},
            ],
        )
        write_jsonl(
            run_dir / "sources.jsonl",
            [source("SRC-0001", "https://hearthstone.blizzard.com/news/1", "LIN-A", verified=True, run_dir=run_dir)],
        )
        write_jsonl(
            run_dir / "evidence.jsonl",
            [{"evidence_id": "EVD-0001", "source_id": "SRC-0001", "claim_ids": ["CLM-0001"], "relationship": "supporting", "locator": "p1", "evidence_type": "fact", "faithful_paraphrase": "x", "exact_excerpt": "Source: SRC-0001 URL: https://hearthstone.blizzard.com/news/1"}],
        )
        write_jsonl(
            run_dir / "claims.jsonl",
            [{"claim_id": "CLM-0001", "claim": "critical thing", "importance": "critical", "status": "supported", "confidence": "HIGH", "supporting_evidence_ids": ["EVD-0001"], "challenging_evidence_ids": [], "challenge_search": {"query_ids": ["QRY-0002"], "result": "none_found"}}],
        )

    def test_anchored_and_challenged_bundle_passes_working(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build(run_dir)
            result = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("exact_excerpt", result.stdout)
            self.assertNotIn("challenge", result.stdout)
            report = search_coverage.analyze(run_dir)
            self.assertEqual(report["anchors"]["anchor_coverage"], 1.0)

    def test_excerpt_not_in_snapshot_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build(run_dir)
            evidence = read_jsonl(run_dir / "evidence.jsonl")
            evidence[0]["exact_excerpt"] = "this sentence does not appear in the snapshot"
            write_jsonl(run_dir / "evidence.jsonl", evidence)
            result = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(result.returncode, 1)
            self.assertIn("exact_excerpt not found in snapshot of SRC-0001", result.stdout)
            evidence[0]["exact_excerpt"] = "Source: SRC"
            write_jsonl(run_dir / "evidence.jsonl", evidence)
            result = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertIn("needs at least 4 words", result.stdout)

    def test_missing_anchor_and_challenge_block_final_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build(run_dir)
            evidence = read_jsonl(run_dir / "evidence.jsonl")
            del evidence[0]["exact_excerpt"]
            write_jsonl(run_dir / "evidence.jsonl", evidence)
            claims = read_jsonl(run_dir / "claims.jsonl")
            del claims[0]["challenge_search"]
            write_jsonl(run_dir / "claims.jsonl", claims)
            working = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(working.returncode, 0, working.stdout)
            self.assertIn("warning: claims.jsonl:1: critical claim has no challenging evidence", working.stdout)
            self.assertIn("warning: claims.jsonl:1: supporting evidence without a verified exact_excerpt", working.stdout)
            final = run(VALIDATE, str(run_dir), "--stage", "final")
            self.assertEqual(final.returncode, 1)
            self.assertIn("- claims.jsonl:1: critical claim has no challenging evidence", final.stdout)
            self.assertIn("- claims.jsonl:1: supporting evidence without a verified exact_excerpt", final.stdout)

    def test_challenge_search_references_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build(run_dir)
            claims = read_jsonl(run_dir / "claims.jsonl")
            claims[0]["challenge_search"] = {"query_ids": ["QRY-0099"], "result": "maybe"}
            write_jsonl(run_dir / "claims.jsonl", claims)
            result = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(result.returncode, 1)
            self.assertIn("references unknown query QRY-0099", result.stdout)
            self.assertIn("challenge_search result is invalid", result.stdout)

    def test_non_canonical_query_values_are_errors_in_12(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build(run_dir)
            queries = read_jsonl(run_dir / "queries.jsonl")
            queries[0]["family"] = "Polish law"
            queries[0]["pass"] = "primary-source"
            del queries[0]["language"]
            write_jsonl(run_dir / "queries.jsonl", queries)
            result = run(VALIDATE, str(run_dir), "--stage", "working")
            self.assertEqual(result.returncode, 1)
            self.assertIn("- queries.jsonl:1: non-canonical query family 'Polish law'", result.stdout)
            self.assertIn("- queries.jsonl:1: non-canonical query pass 'primary-source'", result.stdout)
            self.assertIn("warning: queries.jsonl:1: schema 1.2 query should record a language", result.stdout)

    def test_migration_from_11_to_12_needs_family_map_and_is_reversible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            self.build(run_dir)
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            manifest["schema_version"] = "1.1"
            (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            queries = read_jsonl(run_dir / "queries.jsonl")
            queries[0]["family"] = "Polish law"
            queries[0]["pass"] = "primary-source"
            del queries[0]["language"]
            write_jsonl(run_dir / "queries.jsonl", queries)
            self.assertEqual(run(VALIDATE, str(run_dir), "--stage", "working").returncode, 0)

            refused = run(MIGRATE, str(run_dir), "--to", "1.2")
            self.assertEqual(refused.returncode, 1)
            self.assertIn("family: 'Polish law'", refused.stderr)
            self.assertIn("pass: 'primary-source'", refused.stderr)

            mapping = Path(temp) / "map.json"
            mapping.write_text(json.dumps({"families": {"Polish law": "primary"}, "passes": {"primary-source": "collection"}}), encoding="utf-8")
            preview = run(MIGRATE, str(run_dir), "--to", "1.2", "--family-map", str(mapping))
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))["schema_version"], "1.1")

            applied = run(MIGRATE, str(run_dir), "--to", "1.2", "--family-map", str(mapping), "--apply")
            self.assertEqual(applied.returncode, 0, applied.stderr)
            migrated = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(migrated["schema_version"], "1.2")
            self.assertEqual(migrated["provenance"]["migrated_from"], "1.1")
            queries = read_jsonl(run_dir / "queries.jsonl")
            self.assertEqual(queries[0]["family"], "primary")
            self.assertEqual(queries[0]["legacy_family"], "Polish law")
            self.assertEqual(queries[0]["pass"], "collection")
            self.assertEqual(queries[0]["language"], "en")
            self.assertEqual(run(VALIDATE, str(run_dir), "--stage", "working").returncode, 0)

            backup = next((run_dir / "migration-backups").iterdir())
            rolled = run(MIGRATE, str(run_dir), "--rollback", str(backup))
            self.assertEqual(rolled.returncode, 0, rolled.stderr)
            self.assertEqual(json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))["schema_version"], "1.1")
            self.assertEqual(read_jsonl(run_dir / "queries.jsonl")[0]["family"], "Polish law")
