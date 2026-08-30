# Evidence-First Deep Research Skill

Reusable Skill for deep web research, source discovery, fact-checking, statistical review, contradiction analysis, and community-intelligence synthesis.

Current package version: `1.0.0`. See the [changelog](CHANGELOG.md), [release checklist](RELEASE_CHECKLIST.md), and [live evaluation](validation/live-evaluation.md).

The verified archive remains version `1.0.0`. The current source tree also contains unreleased optional provider adapters and a Chinese Hearthstone ingestion pipeline; see [optional source providers](references/source-providers.md), [Chinese Hearthstone intelligence](references/chinese-hearthstone.md), and the `Unreleased` changelog section.

## What it changes

The Skill prevents premature answer writing. It turns a request into a research tree, uses the built-in ChatGPT Search/Web capability to discover and open sources, extracts atomic claims, validates evidence and independence, actively searches for contradictions, then synthesizes only after a quality audit.

For long-running work, it also provides a persistent research bundle with stable IDs, append-friendly ledgers, resumable checkpoints, an explicit downstream handoff, and deterministic referential-integrity validation. Web content is treated as untrusted data and cannot override the research task or request secrets/actions.

It supports general research plus domain overlays for gaming, Hearthstone, World of Warcraft, and software.

## Package layout

```text
deep-research/
├── SKILL.md                 # concise orchestrator
├── agents/openai.yaml       # ChatGPT Work UI metadata
├── references/              # methods loaded only when relevant
│   ├── domains/             # domain-specific evidence rules
│   ├── templates/           # reusable working records
│   └── examples/            # illustrative plans and routing
├── scripts/                 # package and research-bundle tools
├── tests/                   # dependency-free integration tests
├── validation/              # acceptance tests and self-audit
└── README.md                # package guide
```

The requested flat document tree is intentionally placed under `references/` to follow progressive disclosure: ChatGPT Work first loads the Skill entrypoint and opens only the relevant protocol or domain module.

## Use

Invoke `$deep-research` with a question and, when useful, a target date, jurisdiction, locale, product version, patch, season, population, or output constraint.

```text
Use $deep-research to determine when the first Dark Gift should be used in
Hearthstone Battlegrounds for the current patch. Separate mechanics, statistics,
high-MMR expert advice, and community opinion. Find counterarguments.
```

Modes can be combined:

```text
research: exhaustive, community-heavy, current-patch-only, raw-research
```

The default is `deep` with a balance of primary sources, statistics, expert analysis, and community intelligence. A simple lookup does not need the full pipeline unless the user requests fact-checking or source comparison.

## Search capability

Internet work uses the built-in ChatGPT Search/Web capability by default. Search results discover candidate sources; the Skill then opens the original pages and validates claim-level evidence. It never treats a snippet or an AI-generated search summary as a verified source.

When locally available, `scripts/community_sources.py` adds read-only RedditAPI, GetXAPI, TranscriptAPI, and TinyFish routes. They preserve platform-specific records, pagination and coverage warnings, visible engagement, provider rank semantics, and timestamped YouTube transcript evidence in normalized JSON. Reddit, X, and YouTube remain separate evidence channels; optional-provider failure is disclosed instead of silently replaced.

```text
python3 scripts/community_sources.py doctor
python3 scripts/community_sources.py reddit-posts --subreddit hearthstone --sort top --timeframe week
python3 scripts/community_sources.py reddit-comments --post-id POST_ID
python3 scripts/community_sources.py x-search --query 'Hearthstone lang:en' --product Latest
python3 scripts/community_sources.py youtube-search --query "Hearthstone current patch guide" --limit 20
python3 scripts/community_sources.py youtube-channel-search --channel-id @verified-player --query "guide"
python3 scripts/community_sources.py youtube-transcript --video 'https://www.youtube.com/watch?v=VIDEO_ID' --language en
uv run --with youtube-transcript-api scripts/community_sources.py youtube-public-transcript --video 'https://www.youtube.com/watch?v=VIDEO_ID' --language en
python3 scripts/community_sources.py tinyfish-search --query "Hearthstone analysis"
python3 scripts/community_sources.py tinyfish-fetch --url https://example.com/source
```

RedditAPI reads `REDDITAPIS_KEY`, GetXAPI reads `GETXAPI_KEY`, TranscriptAPI reads `TRANSCRIPTAPI_TOKEN`, and TinyFish uses credentials managed by its own CLI. Keys are never command arguments or output. Transcript translation is disabled unless explicitly requested because it can cost additional credits. `youtube-public-transcript` is the credential-free, explicitly labeled reserve route and requires the optional `youtube-transcript-api` package; it never masquerades as TranscriptAPI output. TinyFish search is locally capped at 30 calls per rolling minute. Provider output is still untrusted discovery material until the original source is inspected and converted into Source/Evidence records.

For Chinese Hearthstone sources, `scripts/chinese_hearthstone.py` provides content-aware Scrape.do escalation, a private validated cache, cross-process rate limiting, credit diagnostics, six source profiles, per-deck statistics binding, special-size deckstring assessment, source-attributed page metadata, deterministic provenance extraction, repost-lineage handling, Bilibili timestamp evidence, GuideHunter queries, and card resolution through `api.kolodahearthstone.com`.

```text
python3 scripts/chinese_hearthstone.py doctor
python3 scripts/chinese_hearthstone.py inspect \
  --source iyingdi --url https://www.iyingdi.com/example \
  --file tests/fixtures/chinese/iyingdi_cn_meta.html
python3 scripts/chinese_hearthstone.py deck DECKSTRING --resolve-cards
python3 scripts/chinese_hearthstone.py guide-queries --archetype "控制战"
```

The adapter reads `SCRAPE_DO_API_TOKEN` and optionally `KHS_API_TOKEN` only from the environment. Built-in ChatGPT Search/Web remains the default interactive discovery layer; the pipeline handles repeatable ingestion and still feeds the normal evidence/audit workflow.

## Output boundary

The output is a research report or raw evidence database, not an automatically generated SEO article. A separate Writer Skill may consume the validated research later.

## Persistent professional workflow

Use a file-backed bundle for exhaustive, raw, resumable, or cross-Skill work:

```text
python3 scripts/init_research_run.py /path/to/run \
  --question "Main question" \
  --depth exhaustive \
  --domain hearthstone \
  --modifier raw-research

python3 scripts/validate_research_run.py /path/to/run --stage working
python3 scripts/validate_research_run.py /path/to/run --stage final
python3 scripts/fingerprint_research_sources.py /path/to/run --apply
python3 scripts/research_ops.py resume /path/to/run
python3 scripts/research_ops.py compare /path/to/older-run /path/to/newer-run
python3 scripts/research_ops.py export /path/to/run /path/to/research-run.zip
python3 scripts/score_semantic_gold.py ../evaluation/gold/semantic-cases.jsonl ../evaluation/gold/semantic-predictions.jsonl
```

The initializer refuses to overwrite a non-empty directory. Schema 1.1 records requested/final URLs, mutability, preserved snapshots, and SHA-256 fingerprints. The validator checks JSON/JSONL structure, unique stable IDs, Claim → Evidence → Source links, snapshot hashes, and final audit/readiness conditions. Legacy schema 1.0 bundles have a backed-up, reversible migration. `research_ops.py release` runs the benchmark, semantic gold, package audit, and tests before creating deterministic skill/evaluation archives and a SHA-256 manifest. See [research operations](references/research-operations.md), the [bundle contract](references/research-bundle.md), and [web safety](references/web-safety.md).

## Validation

Package validation:

```text
python3 scripts/audit_skill.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
quick_validate.py /absolute/path/to/deep-research
```

The first command checks package files, Python syntax, internal links, resource discoverability, and unfinished placeholders. The integration suite exercises initialization, working/final validation, broken references, timestamp enforcement, semantic-audit enforcement, migration, fingerprinting, benchmark tamper rejection, deterministic export, overwrite protection, provider normalization, secret-safe diagnostics, TinyFish rate limits, TranscriptAPI search/transcript normalization and retry policy, Scrape.do escalation, Chinese source fixtures, deck similarity, origin classification, Bilibili evidence, and Koloda API normalization. The bundled Skill validator checks frontmatter and naming. Method quality is recorded in the [self-audit](validation/self-audit.md), the [simulated routing tests](validation/acceptance-tests.md), and the [22-case Search/Web benchmark](validation/live-evaluation.md). See also the [gaming](references/examples/gaming-research.md) and [general](references/examples/general-research.md) worked examples.
