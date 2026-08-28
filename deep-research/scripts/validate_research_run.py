#!/usr/bin/env python3
"""Validate a persistent deep-research bundle and its ID references."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "manifest.json",
    "queries.jsonl",
    "sources.jsonl",
    "evidence.jsonl",
    "claims.jsonl",
    "community.jsonl",
    "contradictions.jsonl",
    "checkpoints.jsonl",
    "audit.json",
    "report.md",
    "handoff.md",
)

STATUS_VALUES = {
    "planned",
    "discovering",
    "collecting",
    "validating",
    "auditing",
    "complete",
    "incomplete",
    "blocked",
}
CLAIM_STATUSES = {
    "supported",
    "supported_with_conditions",
    "contested",
    "unsupported",
    "unresolved",
    "rejected",
}
CONFIDENCE_VALUES = {"VERY_HIGH", "HIGH", "MEDIUM", "LOW", "SPECULATIVE"}
SCHEMA_VALUES = {"1.0", "1.1"}
FINGERPRINT_STATUSES = {"verified", "unavailable", "exempt"}
FINGERPRINT_POLICIES = {"required", "when-permitted", "off"}
SEMANTIC_SUPPORT_VALUES = {"exact", "partial", "none", "contradicted"}
SEMANTIC_REVIEW_VALUES = {"pass", "warning", "fail"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Research-run directory")
    parser.add_argument("--stage", choices=("working", "final"), default="working")
    return parser.parse_args()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name}: root must be an object")
        return {}
    return value


def load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(f"{path.name}: cannot read: {exc}")
        return records
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.name}:{line_number}: record must be an object")
            continue
        value["__line__"] = line_number
        records.append(value)
    return records


def require_fields(
    record: dict[str, Any], fields: tuple[str, ...], label: str, errors: list[str]
) -> None:
    for field in fields:
        if field not in record or record[field] in (None, ""):
            errors.append(f"{label}: missing {field}")


def collect_ids(
    records: list[dict[str, Any]], field: str, prefix: str, ledger: str, errors: list[str]
) -> set[str]:
    values: set[str] = set()
    for record in records:
        line = record.get("__line__", "?")
        value = record.get(field)
        label = f"{ledger}:{line}"
        if not isinstance(value, str) or not value:
            errors.append(f"{label}: missing {field}")
            continue
        if not value.startswith(prefix):
            errors.append(f"{label}: {field} must start with {prefix}")
        if value in values:
            errors.append(f"{label}: duplicate ID {value}")
        values.add(value)
    return values


def require_list(record: dict[str, Any], field: str, label: str, errors: list[str]) -> list[Any]:
    value = record.get(field)
    if not isinstance(value, list):
        errors.append(f"{label}: {field} must be a list")
        return []
    return value


def validate_timestamp(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{label}: timestamp must be a string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label}: invalid ISO-8601 timestamp")


def main() -> int:
    args = parse_args()
    root = Path(args.directory).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        print(f"Research bundle: FAIL\n- not a directory: {root}")
        return 1
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f"missing required file: {name}")
    if errors:
        print("Research bundle: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = load_json(root / "manifest.json", errors)
    schema_hint = manifest.get("schema_version")
    audit = load_json(root / "audit.json", errors)
    queries = load_jsonl(root / "queries.jsonl", errors)
    sources = load_jsonl(root / "sources.jsonl", errors)
    evidence = load_jsonl(root / "evidence.jsonl", errors)
    claims = load_jsonl(root / "claims.jsonl", errors)
    community = load_jsonl(root / "community.jsonl", errors)
    contradictions = load_jsonl(root / "contradictions.jsonl", errors)
    checkpoints = load_jsonl(root / "checkpoints.jsonl", errors)
    semantic_audit: list[dict[str, Any]] = []
    if schema_hint == "1.1":
        semantic_path = root / "semantic-audit.jsonl"
        if not semantic_path.is_file():
            errors.append("missing required file: semantic-audit.jsonl")
        else:
            semantic_audit = load_jsonl(semantic_path, errors)

    require_fields(
        manifest,
        (
            "schema_version",
            "research_id",
            "main_question",
            "created_at",
            "updated_at",
            "as_of",
            "depth",
            "modifiers",
            "domain_adapters",
            "status",
            "current_context",
            "prior_research_ids",
        ),
        "manifest.json",
        errors,
    )
    schema_version = manifest.get("schema_version")
    if schema_version not in SCHEMA_VALUES:
        errors.append("manifest.json: unsupported schema_version")
    if not str(manifest.get("research_id", "")).startswith("RES-"):
        errors.append("manifest.json: research_id must start with RES-")
    if manifest.get("depth") not in {"quick", "deep", "exhaustive"}:
        errors.append("manifest.json: invalid depth")
    if manifest.get("status") not in STATUS_VALUES:
        errors.append("manifest.json: invalid status")
    for field in ("modifiers", "domain_adapters", "prior_research_ids"):
        if not isinstance(manifest.get(field), list):
            errors.append(f"manifest.json: {field} must be a list")
    if not isinstance(manifest.get("current_context"), dict):
        errors.append("manifest.json: current_context must be an object")
    fingerprint_policy = "off"
    if schema_version == "1.1":
        provenance = manifest.get("provenance")
        if not isinstance(provenance, dict):
            errors.append("manifest.json: schema 1.1 requires provenance object")
        else:
            require_fields(
                provenance,
                ("fingerprint_policy", "snapshot_policy", "hash_algorithm"),
                "manifest.json:provenance",
                errors,
            )
            fingerprint_policy = str(provenance.get("fingerprint_policy", ""))
            if fingerprint_policy not in FINGERPRINT_POLICIES:
                errors.append("manifest.json: invalid provenance fingerprint_policy")
            if provenance.get("hash_algorithm") != "sha256":
                errors.append("manifest.json: provenance hash_algorithm must be sha256")
    for field in ("created_at", "updated_at"):
        validate_timestamp(manifest.get(field), f"manifest.json:{field}", errors)
    try:
        date.fromisoformat(str(manifest.get("as_of", "")))
    except ValueError:
        errors.append("manifest.json: as_of must use YYYY-MM-DD")

    query_ids = collect_ids(queries, "query_id", "QRY-", "queries.jsonl", errors)
    source_ids = collect_ids(sources, "source_id", "SRC-", "sources.jsonl", errors)
    evidence_ids = collect_ids(evidence, "evidence_id", "EVD-", "evidence.jsonl", errors)
    claim_ids = collect_ids(claims, "claim_id", "CLM-", "claims.jsonl", errors)
    collect_ids(community, "community_claim_id", "COM-", "community.jsonl", errors)
    collect_ids(contradictions, "contradiction_id", "CTR-", "contradictions.jsonl", errors)
    collect_ids(checkpoints, "checkpoint_id", "CHK-", "checkpoints.jsonl", errors)
    collect_ids(
        semantic_audit,
        "semantic_audit_id",
        "SEM-",
        "semantic-audit.jsonl",
        errors,
    )

    for record in queries:
        label = f"queries.jsonl:{record['__line__']}"
        require_fields(
            record, ("pass", "family", "query", "executed_at", "status"), label, errors
        )
        if record.get("executed_at"):
            validate_timestamp(record.get("executed_at"), f"{label}:executed_at", errors)
        if "result_source_ids" in record:
            for source_id in require_list(record, "result_source_ids", label, errors):
                if source_id not in source_ids:
                    errors.append(f"{label}: unknown result source {source_id}")

    for record in sources:
        label = f"sources.jsonl:{record['__line__']}"
        source_fields = (
            "title",
            "accessed_at",
            "access_integrity",
            "source_type",
            "lineage_id",
        )
        if schema_version == "1.1":
            source_fields += (
                "requested_url",
                "final_url",
                "mutable",
                "fingerprint_status",
            )
        else:
            source_fields += ("url",)
        require_fields(record, source_fields, label, errors)
        urls = (
            (record.get("requested_url"), record.get("final_url"))
            if schema_version == "1.1"
            else (record.get("url"),)
        )
        for url in urls:
            url_text = str(url or "")
            if url_text and not url_text.startswith(("https://", "http://")):
                warnings.append(f"{label}: URL is not HTTP(S)")
        if record.get("accessed_at"):
            validate_timestamp(record.get("accessed_at"), f"{label}:accessed_at", errors)
        if schema_version == "1.1":
            if not isinstance(record.get("mutable"), bool):
                errors.append(f"{label}: mutable must be boolean")
            status = record.get("fingerprint_status")
            if status not in FINGERPRINT_STATUSES:
                errors.append(f"{label}: invalid fingerprint_status")
            if status == "verified":
                require_fields(
                    record,
                    (
                        "content_sha256",
                        "content_bytes",
                        "fingerprinted_at",
                        "snapshot_path",
                    ),
                    label,
                    errors,
                )
                digest = str(record.get("content_sha256", ""))
                if not re.fullmatch(r"[0-9a-f]{64}", digest):
                    errors.append(f"{label}: invalid content_sha256")
                if not isinstance(record.get("content_bytes"), int) or record.get(
                    "content_bytes", -1
                ) < 0:
                    errors.append(f"{label}: content_bytes must be a non-negative integer")
                if record.get("fingerprinted_at"):
                    validate_timestamp(
                        record.get("fingerprinted_at"), f"{label}:fingerprinted_at", errors
                    )
                snapshot_value = record.get("snapshot_path")
                if isinstance(snapshot_value, str) and snapshot_value:
                    snapshot = (root / snapshot_value).resolve()
                    if not snapshot.is_relative_to(root):
                        errors.append(f"{label}: snapshot_path escapes bundle")
                    elif not snapshot.is_file():
                        errors.append(f"{label}: snapshot_path does not exist")
                    else:
                        actual = hashlib.sha256(snapshot.read_bytes()).hexdigest()
                        if digest and actual != digest:
                            errors.append(f"{label}: snapshot hash does not match content_sha256")
            elif status in {"unavailable", "exempt"}:
                require_fields(record, ("fingerprint_reason",), label, errors)

    for record in evidence:
        label = f"evidence.jsonl:{record['__line__']}"
        require_fields(
            record,
            ("source_id", "claim_ids", "relationship", "locator", "evidence_type"),
            label,
            errors,
        )
        if not record.get("faithful_paraphrase") and not record.get("exact_excerpt"):
            errors.append(f"{label}: needs faithful_paraphrase or exact_excerpt")
        if record.get("source_id") not in source_ids:
            errors.append(f"{label}: unknown source {record.get('source_id')}")
        for claim_id in require_list(record, "claim_ids", label, errors):
            if claim_id not in claim_ids:
                errors.append(f"{label}: unknown claim {claim_id}")

    for record in claims:
        label = f"claims.jsonl:{record['__line__']}"
        require_fields(
            record,
            (
                "claim",
                "importance",
                "status",
                "confidence",
                "supporting_evidence_ids",
                "challenging_evidence_ids",
            ),
            label,
            errors,
        )
        if record.get("status") not in CLAIM_STATUSES:
            errors.append(f"{label}: invalid claim status")
        if record.get("confidence") not in CONFIDENCE_VALUES:
            errors.append(f"{label}: invalid confidence")
        linked = []
        for field in ("supporting_evidence_ids", "challenging_evidence_ids"):
            for evidence_id in require_list(record, field, label, errors):
                linked.append(evidence_id)
                if evidence_id not in evidence_ids:
                    errors.append(f"{label}: unknown evidence {evidence_id}")
        if args.stage == "final" and record.get("importance") in {"critical", "material"}:
            if record.get("status") == "unsupported" and record.get("importance") == "critical":
                errors.append(f"{label}: critical claim is unsupported")
            if record.get("status") != "rejected" and not linked:
                errors.append(f"{label}: decision-relevant claim has no linked evidence")
            if record.get("status") == "unresolved" and not record.get("impact_on_main_answer"):
                errors.append(f"{label}: unresolved claim needs impact_on_main_answer")

    evidence_by_id = {record["evidence_id"]: record for record in evidence if record.get("evidence_id")}
    claims_by_id = {record["claim_id"]: record for record in claims if record.get("claim_id")}
    for evidence_id, record in evidence_by_id.items():
        for claim_id in record.get("claim_ids", []):
            claim = claims_by_id.get(claim_id)
            if not claim:
                continue
            reverse_links = claim.get("supporting_evidence_ids", []) + claim.get(
                "challenging_evidence_ids", []
            )
            if evidence_id not in reverse_links:
                errors.append(
                    f"evidence {evidence_id}: claim {claim_id} lacks reciprocal evidence link"
                )
    for claim_id, record in claims_by_id.items():
        for evidence_id in record.get("supporting_evidence_ids", []) + record.get(
            "challenging_evidence_ids", []
        ):
            item = evidence_by_id.get(evidence_id)
            if item and claim_id not in item.get("claim_ids", []):
                errors.append(
                    f"claim {claim_id}: evidence {evidence_id} lacks reciprocal claim link"
                )

    semantic_by_claim: dict[str, list[dict[str, Any]]] = {}
    for record in semantic_audit:
        label = f"semantic-audit.jsonl:{record['__line__']}"
        require_fields(
            record,
            (
                "claim_id",
                "evidence_id",
                "source_id",
                "semantic_support",
                "scope_match",
                "authority_match",
                "freshness_match",
                "evidence_type_match",
                "reviewer_status",
                "reviewer_basis",
                "audited_at",
            ),
            label,
            errors,
        )
        claim_id = record.get("claim_id")
        evidence_id = record.get("evidence_id")
        source_id = record.get("source_id")
        if claim_id not in claim_ids:
            errors.append(f"{label}: unknown claim {claim_id}")
        if evidence_id not in evidence_ids:
            errors.append(f"{label}: unknown evidence {evidence_id}")
        if source_id not in source_ids:
            errors.append(f"{label}: unknown source {source_id}")
        evidence_record = evidence_by_id.get(str(evidence_id))
        if evidence_record:
            if evidence_record.get("source_id") != source_id:
                errors.append(f"{label}: source_id does not match evidence source")
            if claim_id not in evidence_record.get("claim_ids", []):
                errors.append(f"{label}: evidence is not linked to claim")
        if record.get("semantic_support") not in SEMANTIC_SUPPORT_VALUES:
            errors.append(f"{label}: invalid semantic_support")
        if record.get("reviewer_status") not in SEMANTIC_REVIEW_VALUES:
            errors.append(f"{label}: invalid reviewer_status")
        for field in (
            "scope_match",
            "authority_match",
            "freshness_match",
            "evidence_type_match",
        ):
            if not isinstance(record.get(field), bool):
                errors.append(f"{label}: {field} must be boolean")
        if record.get("audited_at"):
            validate_timestamp(record.get("audited_at"), f"{label}:audited_at", errors)
        if record.get("semantic_support") in {"none", "contradicted"} and record.get(
            "reviewer_status"
        ) == "pass":
            errors.append(f"{label}: unsupported evidence cannot have reviewer_status pass")
        semantic_by_claim.setdefault(str(claim_id), []).append(record)

    for record in community:
        label = f"community.jsonl:{record['__line__']}"
        require_fields(record, ("community_claim", "consensus_strength"), label, errors)
        for evidence_id in record.get("supporting_evidence_ids", []):
            if evidence_id not in evidence_ids:
                errors.append(f"{label}: unknown evidence {evidence_id}")

    for record in contradictions:
        label = f"contradictions.jsonl:{record['__line__']}"
        require_fields(record, ("claim_id", "outcome"), label, errors)
        if record.get("claim_id") not in claim_ids:
            errors.append(f"{label}: unknown claim {record.get('claim_id')}")
        for evidence_id in record.get("counter_evidence_ids", []):
            if evidence_id not in evidence_ids:
                errors.append(f"{label}: unknown evidence {evidence_id}")

    for record in checkpoints:
        label = f"checkpoints.jsonl:{record['__line__']}"
        require_fields(
            record,
            (
                "pass",
                "created_at",
                "what_we_know",
                "missing_data",
                "underrepresented_source_types",
                "unsupported_decision_relevant_claims",
                "unresolved_contradictions",
                "freshness_risks",
                "saturated_branches",
                "unsaturated_branches",
                "next_actions",
            ),
            label,
            errors,
        )
        if record.get("created_at"):
            validate_timestamp(record.get("created_at"), f"{label}:created_at", errors)
        for field in (
            "what_we_know",
            "missing_data",
            "underrepresented_source_types",
            "unsupported_decision_relevant_claims",
            "unresolved_contradictions",
            "freshness_risks",
            "saturated_branches",
            "unsaturated_branches",
            "next_actions",
        ):
            require_list(record, field, label, errors)

    audit_status = audit.get("audit_status")
    if args.stage == "final":
        if manifest.get("status") not in {"complete", "incomplete"}:
            errors.append("manifest.json: final stage requires complete or incomplete status")
        if audit_status not in {"pass", "pass_with_warnings"}:
            errors.append("audit.json: final stage requires pass or pass_with_warnings")
        for name, marker in (
            ("report.md", "not-yet-synthesized"),
            ("handoff.md", "not-yet-audited"),
        ):
            text = (root / name).read_text(encoding="utf-8")
            if marker in text or len(text.strip()) < 80:
                errors.append(f"{name}: final content is missing")
        if not claims:
            warnings.append("final bundle contains no claim records")
        if not sources:
            warnings.append("final bundle contains no source records")
        if schema_version == "1.0":
            warnings.append("legacy schema 1.0 bundle; migrate to 1.1 for reproducible sources")
        if schema_version == "1.1":
            mutable_unverified = [
                record.get("source_id", "unknown")
                for record in sources
                if record.get("mutable") is True
                and record.get("fingerprint_status") != "verified"
            ]
            if mutable_unverified and fingerprint_policy == "required":
                errors.append(
                    "mutable sources lack verified fingerprints: "
                    + ", ".join(str(item) for item in mutable_unverified)
                )
            elif mutable_unverified and fingerprint_policy == "when-permitted":
                warnings.append(
                    "mutable sources without verified fingerprints: "
                    + ", ".join(str(item) for item in mutable_unverified)
                )
            for claim_id, claim in claims_by_id.items():
                if claim.get("importance") not in {"critical", "material"}:
                    continue
                if claim.get("status") == "rejected":
                    continue
                reviews = semantic_by_claim.get(claim_id, [])
                if claim.get("importance") == "critical":
                    acceptable = any(
                        item.get("semantic_support") == "exact"
                        and item.get("reviewer_status") == "pass"
                        and all(
                            item.get(field) is True
                            for field in (
                                "scope_match",
                                "authority_match",
                                "freshness_match",
                                "evidence_type_match",
                            )
                        )
                        for item in reviews
                    )
                else:
                    acceptable = any(
                        item.get("semantic_support") in {"exact", "partial"}
                        and item.get("reviewer_status") in {"pass", "warning"}
                        and item.get("scope_match") is True
                        and item.get("freshness_match") is True
                        for item in reviews
                    )
                if not acceptable:
                    errors.append(
                        f"claim {claim_id}: missing acceptable semantic audit for "
                        f"{claim.get('importance')} claim"
                    )
    elif audit_status == "not_run":
        warnings.append("research audit has not run yet")

    if errors:
        print("Research bundle: FAIL")
        for error in errors:
            print(f"- {error}")
        for warning in warnings:
            print(f"- warning: {warning}")
        return 1

    print(
        "Research bundle: PASS "
        f"({len(query_ids)} queries, {len(source_ids)} sources, "
        f"{len(evidence_ids)} evidence items, {len(claim_ids)} claims)"
    )
    for warning in warnings:
        print(f"- warning: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
