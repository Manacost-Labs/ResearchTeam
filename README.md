# ResearchTeam — Evidence-First Deep Research

[![Release](https://img.shields.io/badge/release-1.0.0-0A7B83)](deep-research/CHANGELOG.md)
[![Benchmark](https://img.shields.io/badge/benchmark-22%20cases-success)](evaluation/benchmark/README.md)
[![Semantic Gold](https://img.shields.io/badge/semantic%20gold-100%25-success)](evaluation/gold/semantic-cases.jsonl)
[![License](https://img.shields.io/badge/license-proprietary-lightgrey)](LICENSE)

Production-grade research Skill for ChatGPT Work and Codex. It turns an open-ended question into an auditable evidence pipeline, uses the built-in **ChatGPT Search/Web** capability, verifies sources at claim level, searches for contradictions, and blocks confident delivery when the evidence is incomplete.

## Download

**Main installation package:** [download `deep-research-1.0.0.zip`](release/deep-research-1.0.0.zip)

The separate [evaluation archive](release/deep-research-evaluation-1.0.0.zip) contains the 22-case release oracle and reproducibility evidence. It is not required for normal installation. Archive checksums are recorded in the [release manifest](release/release-manifest.json).

> По-русски: для обычной загрузки в ChatGPT Work используйте основной файл `deep-research-1.0.0.zip`. Evaluation ZIP нужен только для проверки качества релиза.

## What it does

- Builds a recursive research plan before drafting conclusions.
- Separates primary sources, statistics, expert interpretation, community evidence, and counter-evidence.
- Preserves atomic `Claim → Evidence → Source` relationships.
- Tracks freshness, versions, patches, dates, jurisdictions, samples, and source lineage.
- Treats every web page and embedded instruction as untrusted evidence.
- Distinguishes Reddit, forums, X, and other communities instead of flattening them into one “consensus.”
- Returns `ready`, `ready_with_warnings`, or `not_ready` based on explicit quality gates.
- Supports resumable research bundles, deterministic export, comparison, and downstream handoff.

```text
Question
  -> Research tree
  -> ChatGPT Search/Web discovery
  -> Inspected sources + provenance snapshots
  -> Atomic evidence and claims
  -> Contradiction + semantic audit
  -> Report + explicit delivery boundary
```

## Verified release quality

Version `1.0.0` is backed by 20 live Search/Web scenarios across five domains and two controlled adversarial fixtures.

| Release gate | Result |
|---|---:|
| Benchmark cases | 22 |
| Live cases | 20 |
| Critical claims traceable | 48 / 48 |
| Material claims semantically supported | 7 / 7 |
| Mutable sources fingerprinted | 64 / 64 |
| Semantic gold field/verdict accuracy | 100% / 100% |
| Snippet evidence | 0 |
| False-ready decisions | 0 |
| Web-safety violations | 0 |
| Automated tests | 16 passing |

The benchmark validator recomputes these metrics from the linked schema 1.1 bundles. Editing `results.jsonl` cannot manufacture a passing release.

## Install

### ChatGPT Work

Download [the main ZIP](release/deep-research-1.0.0.zip) and upload it through the custom Skill interface available in your ChatGPT Work workspace.

### Codex local installation

Extract the package into the Codex skills directory:

```bash
mkdir -p ~/.codex/skills
unzip deep-research-1.0.0.zip -d ~/.codex/skills
```

The resulting entrypoint should be:

```text
~/.codex/skills/deep-research/SKILL.md
```

## Use

```text
Use $deep-research to investigate the current state of <topic>.
Separate official facts, statistics, expert interpretation, community views,
and counter-evidence. State the date/version scope and unresolved gaps.
```

Useful modifiers:

```text
research: quick
research: deep, current-patch-only
research: exhaustive, raw-research, contradiction-heavy
research: community-heavy, statistics-heavy
```

## Professional workflow

```bash
# Initialize a persistent schema 1.1 bundle
python3 deep-research/scripts/init_research_run.py /path/to/run \
  --question "Main research question" \
  --depth deep \
  --domain general

# Validate and resume from recorded gaps
python3 deep-research/scripts/research_ops.py resume /path/to/run

# Compare two research snapshots
python3 deep-research/scripts/research_ops.py compare /path/to/old /path/to/new

# Validate and create a deterministic ZIP
python3 deep-research/scripts/research_ops.py export /path/to/run /path/to/run.zip
```

The [bundle contract](deep-research/references/research-bundle.md) defines stable IDs, source fingerprints, semantic-audit records, lifecycle states, and readiness rules.

## Search boundary

Internet research uses the built-in **ChatGPT Search/Web** capability. Search snippets and AI-generated search summaries are discovery leads only. A claim may be cited only after the original source is opened and inspected. The Skill does not authorize logins, paywall bypasses, posting, purchasing, or external system changes.

## Repository structure

```text
.
├── deep-research/             # installable Skill source
│   ├── SKILL.md               # runtime entrypoint
│   ├── references/            # methods, domain adapters, templates
│   ├── scripts/               # validation and operations
│   └── tests/                 # dependency-free regression tests
├── evaluation/
│   ├── benchmark/             # 22 release-oracle cases and bundles
│   └── gold/                  # semantic/citation gold set
└── release/                   # deterministic 1.0.0 archives and hashes
```

## Validate from source

```bash
python3 deep-research/scripts/audit_skill.py
python3 -m unittest discover -s deep-research/tests -p 'test_*.py' -v
python3 deep-research/scripts/validate_benchmark.py evaluation/benchmark --stage release
python3 deep-research/scripts/score_semantic_gold.py \
  evaluation/gold/semantic-cases.jsonl \
  evaluation/gold/semantic-predictions.jsonl
```

## Release integrity

```text
deep-research-1.0.0.zip
SHA-256 6c029e2a28b1e400bf1bb9bfd080125698ab7b97462117f60aefbd0840d4ef7e

deep-research-evaluation-1.0.0.zip
SHA-256 1263f6a8f05d24378f6ef4583e06cfcb52ee9cd2c0e1e88a1dd56008ff93a963
```

## License

Proprietary source-available license for private and internal organizational use. Redistribution or publication requires prior written permission. See [LICENSE](LICENSE).
