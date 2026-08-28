# Persistent Research Bundle

## Purpose

The bundle is an optional, portable evidence database for long-running or writer-facing work. It preserves provenance and makes structural errors detectable. It does not replace semantic verification or the Research Auditor.

## Initialize and validate

```text
python3 scripts/init_research_run.py RUN_DIRECTORY \
  --question "MAIN QUESTION" \
  --depth exhaustive \
  --domain hearthstone \
  --modifier raw-research \
  --modifier current-patch-only

python3 scripts/validate_research_run.py RUN_DIRECTORY --stage working
python3 scripts/validate_research_run.py RUN_DIRECTORY --stage final

python3 scripts/fingerprint_research_sources.py RUN_DIRECTORY --apply
python3 scripts/migrate_research_bundle.py LEGACY_RUN --apply
```

The initializer refuses to overwrite a non-empty directory.

## Directory contract

```text
research-run/
├── manifest.json
├── snapshots/              # optional preserved inspected content
├── migration-backups/      # created only by applied migrations
├── queries.jsonl
├── sources.jsonl
├── evidence.jsonl
├── claims.jsonl
├── community.jsonl
├── contradictions.jsonl
├── checkpoints.jsonl
├── semantic-audit.jsonl
├── audit.json
├── report.md
└── handoff.md
```

JSON Lines ledgers contain one JSON object per line. This keeps large runs append-friendly and reviewable.

## Manifest contract

Required fields:

```json
{
  "schema_version": "1.1",
  "research_id": "RES-...",
  "main_question": "...",
  "created_at": "ISO-8601 UTC",
  "updated_at": "ISO-8601 UTC",
  "as_of": "YYYY-MM-DD",
  "depth": "quick | deep | exhaustive",
  "modifiers": [],
  "domain_adapters": [],
  "status": "planned | discovering | collecting | validating | auditing | complete | incomplete | blocked",
  "current_context": {},
  "prior_research_ids": [],
  "provenance": {
    "fingerprint_policy": "required | when-permitted | off",
    "snapshot_policy": "local-only",
    "hash_algorithm": "sha256"
  }
}
```

Schema `1.0` remains readable for legacy validation. New runs use `1.1`. Migrate with a dry-run first; `--apply` creates a timestamped backup under `migration-backups/`, and `--rollback BACKUP_DIRECTORY` restores the two migrated ledgers.

## Minimum ledger contracts

### Query

`query_id`, `pass`, `family`, `query`, `executed_at`, `status`, and optional `result_source_ids`.

### Source

Schema `1.1` requires `source_id`, `title`, `requested_url`, `final_url`, `accessed_at`, `access_integrity`, `source_type`, `lineage_id`, `mutable`, and `fingerprint_status`.

For `verified`, also record `snapshot_path`, `content_sha256`, `content_bytes`, and `fingerprinted_at`. The validator recalculates the hash. For `unavailable` or `exempt`, record `fingerprint_reason`. Never preserve authenticated pages, private session data, paywalled content without permission, or copyrighted material beyond what the research task permits.

### Evidence

`evidence_id`, `source_id`, `claim_ids`, `relationship`, `locator`, `evidence_type`, and either a faithful paraphrase or a compliant excerpt.

### Claim

`claim_id`, `claim`, `importance`, `status`, `confidence`, `supporting_evidence_ids`, `challenging_evidence_ids`, plus scope and impact fields when relevant.

### Community and contradiction records

Use `community_claim_id` or `contradiction_id` and the corresponding template fields. Keep source/evidence IDs rather than copying unsupported prose.

### Checkpoint

`checkpoint_id`, `pass`, `created_at`, the five gap-detection lists, saturated/unsaturated branches, and next actions.

### Semantic audit

Schema `1.1` uses `semantic_audit_id`, `claim_id`, `evidence_id`, `source_id`, `semantic_support`, the four match booleans, `reviewer_status`, `reviewer_basis`, and `audited_at`. Use the [semantic audit template](templates/semantic-audit.md). Critical claims require an exact passing record at final validation; material claims may use a scoped partial warning.

## Validator guarantees

The deterministic validator checks:

- required files and parseable JSON/JSONL;
- required manifest values and allowed lifecycle states;
- ID uniqueness;
- evidence-to-source and evidence-to-claim references;
- claim-to-evidence references;
- basic required fields;
- execution/access timestamps and checkpoint gap-list shapes;
- schema 1.1 provenance policy, snapshot containment, SHA-256 shape, and actual snapshot hash;
- semantic-audit references, verdict values, match fields, and final critical/material coverage;
- final audit/readiness conditions.

It cannot prove that a source is authoritative, an excerpt is faithful, a claim is true, or a conclusion is well reasoned. Those remain evidence-protocol and Auditor responsibilities.

## Final-stage requirements

At `final` stage:

- manifest status is `complete` or `incomplete`;
- audit status is `pass` or `pass_with_warnings`;
- every critical/material non-rejected claim has linked evidence;
- unsupported critical claims are absent;
- unresolved critical claims state their impact on the main answer;
- `report.md` and `handoff.md` contain non-placeholder content.

An incomplete but honest run can validate structurally; its handoff must remain `not_ready` for strong downstream claims.

When `fingerprint_policy` is `required`, an unverified mutable source blocks final validation. `when-permitted` emits a warning. Use `off` only when persistence is explicitly unnecessary or prohibited; it cannot satisfy the 1.0 release benchmark for mutable sources.
