#!/usr/bin/env python3
"""Measure search completeness for a research bundle.

The bundle validator proves structure. This report measures whether the search
itself was broad enough: query families per branch, planned-versus-executed
queries, candidate handling, host and lineage diversity, challenge coverage for
critical claims, and fingerprint coverage. It cannot judge whether the found
sources are the right ones; it makes narrow searching visible.

Exit code is 1 only with ``--strict`` and at least one blocking finding.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from search_support import (
    CANDIDATE_DECISIONS,
    FAMILY_MINIMUMS,
    QUERY_FAMILIES,
    QUERY_PASSES,
    normalize_query,
    url_host,
)

ALL_BRANCH = "__all__"
SNIPPET_INTEGRITY_VALUES = frozenset({"snippet", "search_snippet", "snippet_only"})
TOP_HOST_SHARE_LIMIT = 0.5
TOP_HOST_MIN_SOURCES = 6
EMPTY_QUERY_SHARE_LIMIT = 0.5


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Research bundle directory")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report")
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 when a blocking finding exists"
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                records.append(item)
    return records


def string_list(record: dict[str, Any], field: str) -> list[str]:
    value = record.get(field)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 3)


def analyze(root: Path) -> dict[str, Any]:
    manifest = load_json(root / "manifest.json")
    plan = load_json(root / "plan.json")
    queries = load_jsonl(root / "queries.jsonl")
    planned = load_jsonl(root / "query-plan.jsonl")
    candidates = load_jsonl(root / "candidates.jsonl")
    sources = load_jsonl(root / "sources.jsonl")
    evidence = load_jsonl(root / "evidence.jsonl")
    claims = load_jsonl(root / "claims.jsonl")

    depth = str(manifest.get("depth", "deep"))
    coverage_enabled = "coverage_contract_version" in manifest
    errors: list[str] = []
    warnings: list[str] = []

    # --- queries -----------------------------------------------------------
    executed_queries = [record for record in queries if record.get("status") != "planned"]
    family_counter: Counter[str] = Counter()
    pass_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    language_counter: Counter[str] = Counter()
    non_canonical_family: list[str] = []
    non_canonical_pass: list[str] = []
    with_results = 0
    result_links = 0
    source_ids_by_query: dict[str, list[str]] = {}
    for record in executed_queries:
        query_id = str(record.get("query_id", "?"))
        family = record.get("family")
        family_key = family if isinstance(family, str) and family in QUERY_FAMILIES else "uncategorized"
        if family_key == "uncategorized":
            non_canonical_family.append(query_id)
        family_counter[family_key] += 1
        pass_value = record.get("pass")
        if not (isinstance(pass_value, str) and pass_value in QUERY_PASSES):
            non_canonical_pass.append(query_id)
        pass_counter[str(pass_value)] += 1
        status_counter[str(record.get("status"))] += 1
        language_counter[str(record.get("language", "unspecified"))] += 1
        linked = string_list(record, "result_source_ids")
        source_ids_by_query[query_id] = linked
        if linked:
            with_results += 1
            result_links += len(linked)

    executed_keys = {normalize_query(str(record.get("query", ""))) for record in executed_queries}
    unexecuted = [
        str(record.get("query_id", "?"))
        for record in planned
        if normalize_query(str(record.get("query", ""))) not in executed_keys
    ]

    # --- branches ----------------------------------------------------------
    section_ids: list[str] = []
    section_status: dict[str, str] = {}
    for item in plan.get("deliverable_outline", []) if coverage_enabled else []:
        if isinstance(item, dict) and isinstance(item.get("section_id"), str):
            section_ids.append(item["section_id"])
            section_status[item["section_id"]] = str(item.get("status", ""))
    branch_ids = section_ids or [ALL_BRANCH]
    branch_families: dict[str, set[str]] = {branch: set() for branch in branch_ids}
    branch_queries: Counter[str] = Counter()
    branch_sources: dict[str, set[str]] = {branch: set() for branch in branch_ids}
    for record in executed_queries:
        family = record.get("family")
        family_key = family if isinstance(family, str) and family in QUERY_FAMILIES else None
        targets = string_list(record, "deliverable_section_ids") if section_ids else [ALL_BRANCH]
        for branch in targets:
            if branch not in branch_families:
                continue
            branch_queries[branch] += 1
            if family_key:
                branch_families[branch].add(family_key)
            branch_sources[branch].update(string_list(record, "result_source_ids"))

    required = FAMILY_MINIMUMS.get(depth, FAMILY_MINIMUMS["deep"])
    branches_report: dict[str, Any] = {}
    for branch in branch_ids:
        present = sorted(branch_families[branch])
        missing = sorted(required - branch_families[branch])
        branches_report[branch] = {
            "status": section_status.get(branch),
            "queries": branch_queries[branch],
            "sources": len(branch_sources[branch]),
            "families_present": present,
            "missing_families": missing,
        }
        if section_status.get(branch) == "excluded":
            continue
        if missing:
            errors.append(
                f"branch {branch}: missing required {depth} query families: {', '.join(missing)}"
            )

    # --- candidates --------------------------------------------------------
    decision_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()
    for record in candidates:
        decision = str(record.get("decision", "unknown"))
        decision_counter[decision if decision in CANDIDATE_DECISIONS else "unknown"] += 1
        if decision == "rejected":
            reason_counter[str(record.get("reason", "unspecified"))] += 1
    candidates_report = {
        "present": bool(candidates),
        "total": len(candidates),
        "by_decision": dict(decision_counter),
        "rejections_by_reason": dict(reason_counter),
        "open_rate": ratio(decision_counter["opened"], len(candidates)),
    }
    if not candidates and executed_queries:
        warnings.append(
            "no candidates.jsonl: rejected search results are invisible, so recall cannot be assessed"
        )

    # --- sources -----------------------------------------------------------
    host_counter: Counter[str] = Counter()
    lineage_counter: Counter[str] = Counter()
    integrity_counter: Counter[str] = Counter()
    mutable_total = 0
    mutable_verified = 0
    snippet_only: list[str] = []
    host_by_source: dict[str, str] = {}
    lineage_by_source: dict[str, str] = {}
    for record in sources:
        source_id = str(record.get("source_id", "?"))
        url = record.get("final_url") or record.get("requested_url") or record.get("url") or ""
        host = url_host(str(url)) if url else ""
        host_counter[host or "unknown"] += 1
        host_by_source[source_id] = host
        lineage = str(record.get("lineage_id") or f"self:{source_id}")
        lineage_counter[lineage] += 1
        lineage_by_source[source_id] = lineage
        integrity = str(record.get("access_integrity", "unspecified"))
        integrity_counter[integrity] += 1
        if integrity in SNIPPET_INTEGRITY_VALUES:
            snippet_only.append(source_id)
        if record.get("mutable") is True:
            mutable_total += 1
            if record.get("fingerprint_status") == "verified":
                mutable_verified += 1
    top_host, top_count = (host_counter.most_common(1) or [("", 0)])[0]
    top_share = ratio(top_count, len(sources))
    if snippet_only:
        errors.append(f"snippet-only sources recorded as evidence: {', '.join(snippet_only)}")
    if len(sources) >= TOP_HOST_MIN_SOURCES and top_share and top_share > TOP_HOST_SHARE_LIMIT:
        warnings.append(f"host concentration: {top_host} supplies {top_share:.0%} of sources")
    fingerprint_policy = str(manifest.get("provenance", {}).get("fingerprint_policy", ""))
    if mutable_total and mutable_verified < mutable_total:
        message = f"fingerprint coverage {mutable_verified}/{mutable_total} mutable sources"
        if fingerprint_policy == "required":
            errors.append(message + " (policy required)")
        else:
            warnings.append(message)

    # --- claims ------------------------------------------------------------
    evidence_by_id = {str(item.get("evidence_id")): item for item in evidence}
    critical_material = [
        record
        for record in claims
        if record.get("importance") in {"critical", "material"}
        and record.get("status") != "rejected"
    ]
    with_challenge = 0
    unchallenged_critical: list[str] = []
    unchallenged_material: list[str] = []
    single_lineage_critical: list[str] = []
    single_host_critical: list[str] = []
    for record in critical_material:
        claim_id = str(record.get("claim_id", "?"))
        challenge_search = record.get("challenge_search")
        searched = isinstance(challenge_search, dict) and bool(
            string_list(challenge_search, "query_ids")
        )
        if string_list(record, "challenging_evidence_ids") or searched:
            with_challenge += 1
        elif record.get("importance") == "critical":
            unchallenged_critical.append(claim_id)
        else:
            unchallenged_material.append(claim_id)
        if record.get("importance") != "critical":
            continue
        supporting_sources = {
            str(evidence_by_id[evidence_id].get("source_id"))
            for evidence_id in string_list(record, "supporting_evidence_ids")
            if evidence_id in evidence_by_id
        }
        if len(supporting_sources) < 2:
            continue
        lineages = {lineage_by_source.get(source, f"self:{source}") for source in supporting_sources}
        hosts = {host_by_source.get(source, "") for source in supporting_sources}
        if len(lineages) == 1:
            single_lineage_critical.append(claim_id)
        if len(hosts) == 1:
            single_host_critical.append(claim_id)
    if unchallenged_critical:
        errors.append(
            "critical claims without challenging evidence or a recorded challenge search: "
            + ", ".join(unchallenged_critical)
        )
    if unchallenged_material:
        warnings.append(
            "material claims without challenging evidence or a recorded challenge search: "
            + ", ".join(unchallenged_material)
        )
    if single_lineage_critical:
        warnings.append(
            "critical claims whose multiple sources share one lineage: "
            + ", ".join(single_lineage_critical)
        )
    if single_host_critical:
        warnings.append(
            "critical claims whose multiple sources share one host: "
            + ", ".join(single_host_critical)
        )

    # --- query-level warnings ---------------------------------------------
    if executed_queries:
        empty_share = 1 - with_results / len(executed_queries)
        if empty_share > EMPTY_QUERY_SHARE_LIMIT:
            warnings.append(f"{empty_share:.0%} of executed queries link no result sources")
    if non_canonical_family:
        warnings.append(
            f"{len(non_canonical_family)} queries use a non-canonical family and cannot be "
            "counted toward branch coverage"
        )
    if non_canonical_pass:
        warnings.append(f"{len(non_canonical_pass)} queries use a non-canonical pass")
    if unexecuted:
        warnings.append(f"{len(unexecuted)} planned queries were never executed")
    if language_counter and set(language_counter) == {"unspecified"}:
        warnings.append("queries do not record a language; localized coverage is unknown")

    return {
        "research_id": manifest.get("research_id"),
        "depth": depth,
        "coverage_enabled": coverage_enabled,
        "queries": {
            "total": len(executed_queries),
            "by_status": dict(status_counter),
            "by_family": dict(family_counter),
            "by_pass": dict(pass_counter),
            "by_language": dict(language_counter),
            "non_canonical_family": non_canonical_family,
            "non_canonical_pass": non_canonical_pass,
            "with_results": with_results,
            "sources_per_query": ratio(result_links, len(executed_queries)),
        },
        "plan": {
            "present": bool(planned),
            "planned": len(planned),
            "unexecuted": len(unexecuted),
            "unexecuted_ids": unexecuted,
        },
        "candidates": candidates_report,
        "sources": {
            "total": len(sources),
            "hosts": len(host_counter),
            "top_host": top_host,
            "top_host_share": top_share,
            "lineages": len(lineage_counter),
            "mutable_total": mutable_total,
            "mutable_verified": mutable_verified,
            "fingerprint_coverage": ratio(mutable_verified, mutable_total),
            "access_integrity": dict(integrity_counter),
            "snippet_only": snippet_only,
        },
        "claims": {
            "critical_material_total": len(critical_material),
            "with_challenge": with_challenge,
            "challenge_coverage": ratio(with_challenge, len(critical_material)),
            "unchallenged_critical": unchallenged_critical,
            "unchallenged_material": unchallenged_material,
            "single_lineage_critical": single_lineage_critical,
            "single_host_critical": single_host_critical,
        },
        "branches": branches_report,
        "findings": {"errors": errors, "warnings": warnings},
    }


def format_summary(report: dict[str, Any]) -> str:
    queries = report["queries"]
    sources = report["sources"]
    claims = report["claims"]
    findings = report["findings"]
    verdict = "FAIL" if findings["errors"] else "PASS"
    lines = [
        f"Search coverage: {verdict} ({report['depth']}; "
        f"{queries['total']} queries, {sources['total']} sources, "
        f"{sources['hosts']} hosts, {sources['lineages']} lineages)",
        f"- sources per query: {queries['sources_per_query']}",
        f"- families used: {', '.join(sorted(queries['by_family'])) or 'none'}",
        f"- challenge coverage: {claims['with_challenge']}/{claims['critical_material_total']}",
        f"- fingerprint coverage: {sources['mutable_verified']}/{sources['mutable_total']} mutable",
    ]
    if report["plan"]["present"]:
        lines.append(
            f"- plan: {report['plan']['planned']} planned, {report['plan']['unexecuted']} unexecuted"
        )
    if report["candidates"]["present"]:
        lines.append(
            f"- candidates: {report['candidates']['total']} seen, "
            f"open rate {report['candidates']['open_rate']}"
        )
    for branch, item in report["branches"].items():
        missing = ", ".join(item["missing_families"]) or "none"
        lines.append(
            f"- branch {branch}: {item['queries']} queries, {item['sources']} sources, "
            f"missing families: {missing}"
        )
    for error in findings["errors"]:
        lines.append(f"- error: {error}")
    for warning in findings["warnings"]:
        lines.append(f"- warning: {warning}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.directory).expanduser().resolve()
    if not (root / "manifest.json").is_file():
        print(f"error: not a research bundle: {root}", file=sys.stderr)
        return 2
    try:
        report = analyze(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_summary(report))
    if args.strict and report["findings"]["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
