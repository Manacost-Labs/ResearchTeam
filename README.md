<div align="center">

# ResearchTeam

### Evidence-first deep research for ChatGPT Work and Codex

Turn an open-ended question into an auditable chain of sources, evidence, claims, contradictions, and confidence-rated conclusions.

[![Release](https://img.shields.io/badge/release-1.0.0-0A7B83)](deep-research/CHANGELOG.md)
[![Benchmark](https://img.shields.io/badge/benchmark-22%2F22-success)](evaluation/benchmark/README.md)
[![Tests](https://img.shields.io/badge/source%20tests-60%20passing-success)](deep-research/tests)
[![Semantic Gold](https://img.shields.io/badge/semantic%20gold-100%25-success)](evaluation/gold/semantic-cases.jsonl)
[![License](https://img.shields.io/badge/license-proprietary-lightgrey)](LICENSE)

[Download 1.0.0](release/deep-research-1.0.0.zip) ·
[Skill documentation](deep-research/README.md) ·
[Evaluation](evaluation/evaluation-report.md) ·
[Changelog](deep-research/CHANGELOG.md)

</div>

---

## Why ResearchTeam

Most research failures happen before writing: the question is underspecified, search snippets are mistaken for evidence, repeated sources are counted as independent confirmation, or a confident conclusion is produced despite missing statistics and contradictions.

ResearchTeam makes those failure modes explicit and testable. It plans first, collects evidence by claim type, validates provenance and freshness, searches for disconfirming evidence, and permits a strong conclusion only after the quality gate passes.

> **Release boundary:** `deep-research-1.0.0.zip` is the verified stable package. The repository source also contains unreleased read-only adapters for RedditAPI, GetXAPI, TranscriptAPI, TinyFish, and Chinese Hearthstone intelligence. They are not silently included in the 1.0.0 archive.

## Core guarantees

- Research planning happens before conclusion writing.
- Primary sources, statistics, experts, community evidence, and counter-evidence remain separate.
- Every consequential conclusion is traceable through `Claim → Evidence → Source`.
- Publication date, event date, access date, version, patch, sample, and source lineage are preserved when relevant.
- Search snippets and AI summaries are discovery leads, never verified evidence.
- Reddit, X, forums, YouTube, and other communities are not flattened into a fictional universal consensus.
- Missing evidence lowers confidence instead of being hidden.
- The final state is explicit: `ready`, `ready_with_warnings`, or `not_ready`.
- Web content is treated as untrusted data and cannot override the research task or request secrets/actions.

## How it works

```text
Question and scope
  ↓
Recursive research tree
  ↓
Built-in ChatGPT Search/Web + optional specialist sources
  ↓
Opened sources and provenance records
  ↓
Atomic evidence and falsifiable claims
  ↓
Contradiction, freshness, and semantic-support checks
  ↓
Adversarial Research Auditor
  ↓
Research report or reusable evidence bundle
```

The built-in **ChatGPT Search/Web** capability remains the default discovery and source-opening layer. Optional providers improve platform-specific access without weakening the evidence rules.

| Source layer | Purpose | Status |
|---|---|---|
| ChatGPT Search/Web | Default web discovery and source inspection | Included in 1.0.0 |
| RedditAPI | Subreddit listings, search, posts, and comment context | Unreleased source adapter |
| GetXAPI | Direct X posts, dates, authors, and visible engagement | Unreleased source adapter |
| TranscriptAPI | YouTube search, verified-channel discovery, and timestamped transcripts | Unreleased source adapter |
| TinyFish | General web search and clean page extraction | Unreleased source adapter |
| Scrape.do + Chinese profiles | Repeatable IYingdi, TapTap, NGA, Bilibili, GamerSky, and 17173 ingestion | Unreleased source adapter |
| Koloda Hearthstone API | DBF validation and RU/EN card metadata | Unreleased source adapter |

Provider output is not automatically evidence. The original source must still be inspected and attached to a specific claim.

## Quick start

### ChatGPT Work

1. Download the main package: **[`deep-research-1.0.0.zip`](release/deep-research-1.0.0.zip)**.
2. Upload it through the custom Skill interface in your ChatGPT Work workspace.
3. Start with a bounded research request:

```text
Use $deep-research to investigate the current state of <topic>.
Separate official facts, statistics, expert interpretation, community views,
and counter-evidence. State the date/version scope and unresolved gaps.
```

The [evaluation archive](release/deep-research-evaluation-1.0.0.zip) is only for release verification and is not required for installation.

### Codex

Extract the stable package into the local Skills directory:

```bash
mkdir -p ~/.codex/skills
unzip deep-research-1.0.0.zip -d ~/.codex/skills
```

Expected entrypoint:

```text
~/.codex/skills/deep-research/SKILL.md
```

## Research modes

The default mode is `deep`. Modes and modifiers can be combined:

| Mode or modifier | Use when |
|---|---|
| `quick` | The question is narrow and only a few claims are consequential |
| `deep` | The default for multi-branch research and mixed evidence |
| `exhaustive` | A guide, dossier, or reusable evidence base needs recursive coverage |
| `current-patch-only` | Product/game version compatibility is mandatory |
| `community-heavy` | Reddit, X, YouTube, forums, or practitioners are central |
| `statistics-heavy` | Quantitative evidence and methodology are decision-critical |
| `contradiction-heavy` | The topic is disputed, strategic, causal, or superlative |
| `raw-research` | Another Skill or writer will consume the validated evidence later |

Example:

```text
Use $deep-research to determine when the first Dark Gift should be used in
Hearthstone Battlegrounds for the current patch. Separate mechanics,
statistics, high-MMR expert advice, community opinion, and counterarguments.

research: exhaustive, current-patch-only, raw-research
```

## Optional provider adapters

The current source tree exposes a dependency-free, read-only JSON interface:

```bash
# Availability without printing credential values
python3 deep-research/scripts/community_sources.py doctor

# Reddit community sample
python3 deep-research/scripts/community_sources.py reddit-posts \
  --subreddit hearthstone --sort top --timeframe week --limit 25

# X posts through GetXAPI
python3 deep-research/scripts/community_sources.py x-search \
  --query 'Hearthstone since:2026-08-22 lang:en' --product Latest

# General web discovery through TinyFish
python3 deep-research/scripts/community_sources.py tinyfish-search \
  --query "Hearthstone current patch analysis"

# YouTube discovery and a timestamped transcript
python3 deep-research/scripts/community_sources.py youtube-search \
  --query "Hearthstone current patch high legend guide" --limit 20
python3 deep-research/scripts/community_sources.py youtube-transcript \
  --video 'https://www.youtube.com/watch?v=VIDEO_ID' --language en

# Reserve path when TranscriptAPI is unavailable
uv run --with youtube-transcript-api \
  deep-research/scripts/community_sources.py youtube-public-transcript \
  --video 'https://www.youtube.com/watch?v=VIDEO_ID' --language en
```

Credential boundary:

- RedditAPI reads `REDDITAPIS_KEY` from the local environment.
- GetXAPI reads `GETXAPI_KEY` from the local environment.
- TranscriptAPI reads `TRANSCRIPTAPI_TOKEN` from the local environment.
- Public YouTube captions require no credential and are always labeled as an explicit reserve source.
- TinyFish uses credentials managed by its own CLI.
- Keys must never appear in command arguments, URLs, repository files, bundles, snapshots, logs, or output.
- The adapter exposes no login, posting, voting, commenting, direct-message, cookie, or account-modification operation.

TinyFish is locally limited to 30 searches and 150 fetched URLs per rolling minute. Provider cost, rate exhaustion, inaccessible sources, and partial listing coverage remain visible in normalized output. See the full [provider contract](deep-research/references/source-providers.md).

Chinese Hearthstone ingestion is a separate deterministic path:

```bash
# Safe configuration report: values are never printed
python3 deep-research/scripts/chinese_hearthstone.py doctor

# Offline extraction fixture
python3 deep-research/scripts/chinese_hearthstone.py inspect \
  --source iyingdi \
  --url https://www.iyingdi.com/example \
  --file deep-research/tests/fixtures/chinese/iyingdi_cn_meta.html

# Live public source through Scrape.do, with DBF enrichment
python3 deep-research/scripts/chinese_hearthstone.py fetch \
  --source iyingdi \
  --url https://www.iyingdi.com/example \
  --resolve-cards
```

It reads `SCRAPE_DO_API_TOKEN` and optionally `KHS_API_TOKEN` from the environment. It validates actual content before accepting HTTP 200, uses a private validated cache and cross-process local rate limiter, reports provider credits without exposing credentials, escalates `normal → render → super → super+render`, stops dead URLs and account/rate errors, preserves original Chinese, binds each deck to its own statistics block, decodes special-size deckstrings without false corruption errors, tracks repost lineage, and resolves cards through [api.kolodahearthstone.com](https://github.com/Manacost-Labs/api.kolodahearthstone.com). Full methodology and CLI contracts are in [Chinese Hearthstone intelligence](deep-research/references/chinese-hearthstone.md).

## Persistent professional workflow

For exhaustive, resumable, or cross-Skill work, create a schema 1.1 research bundle:

```bash
# Initialize without overwriting a non-empty directory
python3 deep-research/scripts/init_research_run.py /path/to/run \
  --question "Main research question" \
  --depth exhaustive \
  --domain general \
  --modifier raw-research

# Continue from recorded evidence gaps
python3 deep-research/scripts/research_ops.py resume /path/to/run

# Validate before delivery
python3 deep-research/scripts/validate_research_run.py /path/to/run --stage final

# Compare two research snapshots
python3 deep-research/scripts/research_ops.py compare /path/to/old /path/to/new

# Create a deterministic archive
python3 deep-research/scripts/research_ops.py export /path/to/run /path/to/run.zip
```

The [bundle contract](deep-research/references/research-bundle.md) defines stable IDs, provenance snapshots, source fingerprints, semantic-audit records, lifecycle states, and readiness rules.

## Verified quality

The stable 1.0.0 release is backed by 20 live Search/Web scenarios across five domains and two controlled adversarial fixtures.

| Release gate | Verified result |
|---|---:|
| Benchmark cases | 22 / 22 |
| Live cases | 20 |
| Critical claims traceable | 48 / 48 |
| Material claims semantically supported | 7 / 7 |
| Mutable sources fingerprinted | 64 / 64 |
| Semantic gold field/verdict accuracy | 100% / 100% |
| Snippet evidence admitted as proof | 0 |
| False-ready decisions | 0 |
| Web-safety violations | 0 |
| Automated tests in the 1.0.0 release | 16 passing |
| Automated tests in current source | 42 passing |

The release validator recomputes benchmark metrics from the linked research bundles. Editing a summary result cannot manufacture a passing release.

Run the complete source checks:

```bash
python3 deep-research/scripts/audit_skill.py
python3 -m unittest discover -s deep-research/tests -p 'test_*.py' -v
python3 deep-research/scripts/validate_benchmark.py evaluation/benchmark --stage release
python3 deep-research/scripts/score_semantic_gold.py \
  evaluation/gold/semantic-cases.jsonl \
  evaluation/gold/semantic-predictions.jsonl
```

## Repository structure

```text
.
├── deep-research/
│   ├── SKILL.md                 # runtime orchestrator
│   ├── agents/openai.yaml       # ChatGPT Work metadata
│   ├── references/              # protocols, domains, templates, examples
│   ├── scripts/                 # adapters, validation, bundle operations
│   ├── tests/                   # dependency-free regression suite
│   └── validation/              # acceptance tests and self-audit
├── evaluation/
│   ├── benchmark/               # 22 release-oracle cases and bundles
│   └── gold/                    # semantic/citation gold set
└── release/                     # deterministic 1.0.0 archives and manifest
```

## Security model

- Internet content is untrusted evidence, including embedded tool instructions.
- Research access never authorizes login, paywall bypass, purchasing, posting, or external system changes.
- Credentials are environment- or provider-managed and excluded from research artifacts.
- Provider failures degrade explicitly to partial or blocked coverage.
- Scrape.do's provider-required authentication URL is confined to the transport layer and is never emitted, persisted, or copied into diagnostics.
- Structural validators prove integrity and provenance links; they do not pretend to prove factual truth.
- Strong synthesis remains blocked until semantic support and the adversarial audit pass.

## Release integrity

Checksums are also recorded in the [release manifest](release/release-manifest.json).

```text
deep-research-1.0.0.zip
SHA-256 6c029e2a28b1e400bf1bb9bfd080125698ab7b97462117f60aefbd0840d4ef7e

deep-research-evaluation-1.0.0.zip
SHA-256 1263f6a8f05d24378f6ef4583e06cfcb52ee9cd2c0e1e88a1dd56008ff93a963
```

## Roadmap to 1.1.0

- Add sanitized live contract tests for RedditAPI and GetXAPI.
- Add host-level scheduling and durable persistence for Chinese source polling; the current adapter exposes the ingestion contract without introducing a second database architecture.
- Expose the read-only source layer through a host-compatible MCP server.
- Add CI for audit, tests, benchmark, semantic gold, secret scanning, and deterministic packaging.
- Add per-run provider budgets, caching/deduplication, latency, cost, and failure telemetry.
- Rerun the release oracle and publish new deterministic archives and checksums.

## License

Proprietary source-available license for private and internal organizational use. Redistribution or publication requires prior written permission. See [LICENSE](LICENSE).
