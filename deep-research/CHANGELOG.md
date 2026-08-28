# Changelog

## 1.0.0 — 2026-08-28

- Validated 22 release-oracle cases: 20 live ChatGPT Search/Web runs across five domains plus two adversarial fixtures.
- Added schema 1.1 source provenance, local snapshots, SHA-256 fingerprint verification, and reversible schema 1.0 migration.
- Added claim-level semantic/citation auditing and a scored adversarial gold set.
- Added derived benchmark results: release validation recomputes metrics from linked bundles and rejects self-reported metric tampering.
- Added operational `resume`, `compare`, deterministic `export`, and gated `release` commands.
- Added deterministic skill and evaluation archives with SHA-256 release manifests.
- Added explicit proprietary licensing and expanded regression coverage.

## 0.2.0 — 2026-08-28

- Added three live Search/Web evaluation runs for factual, strategic, and exhaustive research.
- Added an evidence-availability gate for missing statistics, experts, and primary evidence.
- Added mandatory disambiguation of overloaded research terms.
- Added Hearthstone-specific separation of offer, shared-copy, generation, and active-content pools.
- Added baseline-plus-patch-overlay freshness rules.
- Hardened bundle validation for execution/access timestamps and checkpoint gap lists.
- Added a regression test for missing query timestamps.

## 0.1.0 — 2026-08-28

- Initial evidence-first research protocol.
- Built-in ChatGPT Search/Web contract.
- Persistent research bundles with stable Claim → Evidence → Source links.
- Research Auditor, contradiction search, freshness, confidence, and domain adapters.
