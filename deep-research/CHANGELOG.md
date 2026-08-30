# Changelog

## Unreleased

- Added a dependency-free Chinese Hearthstone ingestion pipeline for IYingdi, TapTap, NGA, Bilibili, GamerSky, and 17173.
- Added content-aware Scrape.do escalation with bounded retries, target/provider status separation, dead-URL stop rules, cost headers, redacted diagnostics, and browser-fallback state.
- Added deterministic Hearthstone deckstring decoding, validation, fingerprints, 30/29/28/26-card similarity, source-to-deck relationships, and added/removed DBF IDs.
- Added read-only DBF enrichment through `api.kolodahearthstone.com` with optional Bearer authorization from `KHS_API_TOKEN`.
- Added CN statistics, terminology, provenance, origin/repost classification, earliest-observed scope, GuideHunter queries, structured guide evidence, Bilibili timestamp normalization, scoring, health, and metrics contracts.
- Added offline Chinese HTML/JSON fixtures and regression coverage for multi-deck compilations, CAPTCHA/SPA/status failures, secret safety, lineage, classifiers, and card API normalization.
- Added optional read-only RedditAPI, GetXAPI, and TinyFish adapters with normalized JSON output and no stored credentials.
- Added fail-fast local TinyFish limits for 30 searches and 150 fetched URLs per rolling minute.
- Added provider routing, platform-separation, cost/rate, incomplete-coverage, and third-party provenance rules.
- Documented the Google Research assessment: adopt AIS-style attribution methodology, but do not add BLEURT or ScaNN runtime dependencies without a measured need.
- Added offline regression tests for normalization, comment-tree completeness, risk flags, secret-safe diagnostics, and rate limiting.

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
