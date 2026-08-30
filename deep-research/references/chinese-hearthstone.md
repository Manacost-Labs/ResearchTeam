# Chinese Hearthstone Intelligence

## Purpose and boundary

Use this module when Chinese Hearthstone sources are material to a current-patch research question. It ingests public source content into structured, provenance-preserving records; it does not write the final guide, claim that a crawler found the first creator in the world, or treat reposts as independent corroboration.

Built-in ChatGPT Search/Web remains the default discovery and source-inspection layer for interactive research. The local pipeline adds repeatable Chinese-source retrieval through Scrape.do when `SCRAPE_DO_API_TOKEN` is configured. Provider output is still untrusted source material and must pass the normal Claim → Evidence → Source workflow before it supports a conclusion.

## Supported profiles

| Profile | Domains | Role | Default polling interval |
|---|---|---|---:|
| `iyingdi` | `iyingdi.com`, `battle.com`, `mob.battle.com` | primary articles and CN statistics | 3 hours |
| `taptap` | `taptap.cn`, `taptap.com` | community threads, app 213 | 2 hours |
| `nga` | `nga.cn`, `bbs.nga.cn` | community threads and guides | 2 hours |
| `bilibili` | `bilibili.com`, `b23.tv` | videos, subtitles, selected comments | 1 hour |
| `gamersky` | `gamersky.com` | secondary articles and repost discovery | 12 hours |
| `17173` | `17173.com` | compilations and multi-deck articles | 12 hours |

Poll intervals are configuration defaults, not a scheduler. A host application owns queues, clocks, durable state, and concurrency.

## Runtime flow

```text
discover listing or candidate URL
  -> fetch with Scrape.do normal mode
  -> validate status and actual content
  -> render / super / super+render only when needed
  -> clean HTML while retaining original Chinese
  -> extract statistics, deckstrings, provenance, guide evidence
  -> decode deckstrings and create canonical fingerprints
  -> resolve DBF IDs through api.kolodahearthstone.com
  -> classify origin and source lineage
  -> deduplicate source, content, deck, and repost lineage
  -> pass structured evidence to the normal research pipeline
```

The code is in `scripts/chinese_hearthstone.py`. It has no third-party runtime dependency.

## Retrieval and cost control

The Scrape.do client always starts with the cheapest mode and sets `disableRetry=true`; ResearchTeam owns the bounded retry policy. It tests the returned body rather than trusting HTTP 200. CAPTCHA/challenge text, login walls, access blocks, thin pages, malformed JSON, and empty SPA shells remain failures.

The attempt ledger records:

- mode;
- target status;
- elapsed milliseconds;
- `Retry-After` when present;
- `Scrape.do-Request-Cost` when present;
- content-validation reasons.

`Scrape.do-Initial-Status-Code` is treated as the target status. Provider `404/410` results stop immediately and never escalate. Authentication and rate-limit failures also stop rather than changing to a more expensive mode. Missing cost attribution is visible in metrics and is never silently counted as free.

Scrape.do API mode requires its token as an authentication query parameter. The client constructs that provider URL only inside the transport boundary, never returns it, never logs it, and replaces network failures with redacted diagnostics. Do not add debug logging for `Request.full_url`.

This behavior follows the current [Scrape.do API parameters](https://scrape.do/documentation/), [status code](https://scrape.do/documentation/api-response/status-codes/), [retry](https://scrape.do/documentation/api-response/retry-settings/), and [response header](https://scrape.do/documentation/api-response/response-output/) contracts. It also adopts the measured provider/target separation and dead-URL cost rules from the MIT-licensed [Manacost Labs ParsesUnix](https://github.com/Manacost-Labs/ParsesUnix) adapter.

## Deck intelligence

Deckstrings are detected and decoded deterministically as base64 plus unsigned varints. The parser validates the header, version, format, hero, card counts, DBF IDs, trailing data, and sideboard block. It never asks an LLM to parse a deck code.

Each valid deck receives a SHA-256 fingerprint over sorted `DBF_ID:count` pairs. Pairwise comparison uses card-copy overlap:

| Shared copies in two 30-card decks | Relationship |
|---:|---|
| 30 | `EXACT` |
| 29 | `NEAR_DUPLICATE` |
| 28 | `VARIANT` |
| 26–27 | `ARCHETYPE_VARIANT` |
| otherwise | `DISTINCT` |

Added and removed DBF IDs remain explicit.

Card names and classes come from the read-only `GET /api/v1/constructed-cards/by-dbf/{dbf}` contract at [api.kolodahearthstone.com](https://github.com/Manacost-Labs/api.kolodahearthstone.com). Public reads work without a token. If `KHS_API_TOKEN` is configured, it is sent only in `Authorization: Bearer` and never appears in output. A missing DBF ID remains a visible validation gap.

The deck format implementation is compatible with the documented [HearthSim deckstring format](https://hearthsim.info/docs/deckstrings/) and the MIT/ISC-attributed [Manacost Labs deckstring codecs](https://github.com/Manacost-Labs/hearthstone-deckstrings).

## Origin classification

The classifier emits only:

- `CN_ORIGINAL`;
- `CN_VARIANT`;
- `CN_META`;
- `WESTERN_REPOST`;
- `UNKNOWN`.

An explicit `自创`, `原创`, `自己构筑`, or `本人构筑` marker is not enough for `CN_ORIGINAL`. The record must also have a Chinese ladder/result signal and a completed western-match check with no match. `CN_VARIANT` requires a measured deck comparison. `CN_META` requires CN-region statistics. `WESTERN_REPOST` requires attribution/repost signals tied to a known western source.

The crawler stores `earliest_observed_source` with an observation timestamp and the scope `crawler_observation_only`. It never upgrades this into a global authorship claim.

## Structured extraction

The deterministic statistics parser recognizes:

```text
服务器, 总场数, 赢, 输, 胜率, 排名区间,
平均对局时长, 最后更新时间
```

Region mapping is `国服 → CN`, `欧服 → EU`, `美服 → NA`, and `亚服 → ASIA`. The internal terminology dictionary also covers deck, mode, guide, class, ladder, matchup, mulligan, patch, data, author, and source concepts. It assists parsing and classification; it is not UI copy and does not replace translation review.

HTML cleaning removes common navigation, footer, ad, login, recommendation, script, style, SVG, and repeated-layout blocks. Original Chinese clean text and its content hash remain available. Raw HTML is only emitted when the operator explicitly requests it; never persist authenticated, private, or restricted content.

## GuideHunter and Bilibili

`guide-queries` produces exact, localized query families across NGA, TapTap, Bilibili, and IYingdi using `留牌`, `对局`, `攻略`, `国服`, `上分`, and `构筑`. The ingestion contract separates gameplan, mulligan, matchups, card choices, replacements, combos, win conditions, mistakes, meta observations, and author claims.

Bilibili JSON normalization preserves metadata, deckstrings in descriptions, subtitle segments with start/end timestamps, and selected strategy-bearing comments. Each guide evidence record keeps original Chinese, optional Russian translation, source URL, lineage, category, stance, collection time, and confidence. Ingestion must not generate the final guide.

## Commands

```text
# Configuration without printing secret values
python3 scripts/chinese_hearthstone.py doctor

# Offline source inspection
python3 scripts/chinese_hearthstone.py inspect \
  --source iyingdi \
  --url https://www.iyingdi.com/example \
  --file tests/fixtures/chinese/iyingdi_cn_meta.html

# One live public fetch through Scrape.do
python3 scripts/chinese_hearthstone.py fetch \
  --source iyingdi \
  --url https://www.iyingdi.com/example \
  --resolve-cards \
  --output /authorized/path/iyingdi.json

# Deterministic deck decode and DBF resolution
python3 scripts/chinese_hearthstone.py deck DECKSTRING --resolve-cards

# Localized GuideHunter queries
python3 scripts/chinese_hearthstone.py guide-queries --archetype "控制战"
```

The example config is `references/examples/chinese-hearthstone-config.json`. Secrets belong only in environment variables or a secret manager; never put them in that file, command arguments, fixtures, research bundles, or Git.

## Persistence contract

A host that persists output should retain:

```text
source, source_id, source_url, fetched_at, published_at, author, title,
language, clean_text_zh, content_hash, provenance, classification,
deck fingerprint, source-to-deck relationships, lineage_hint,
earliest_observed_source, last successful fetch, last content hash,
last extracted deck fingerprints, parser version
```

Deduplicate content by canonical URL plus content hash, decks by fingerprint, and reposts by lineage. A compilation containing 20 valid codes creates 20 source-to-deck relationships.

## Health and metrics

`pipeline_metrics()` exposes fetched/blocked/rate-limited counts, successes by mode, fallback rate, parser success, valid/invalid/unique/duplicate decks, classifications, provenance rate, average attributed credits, and unattributed-cost attempts. `site_health()` reports the latest state and last-good timestamp for each source profile.

Monitor at least:

- discovery and fetch volume;
- success per escalation mode;
- block, rate-limit, parser-failure, and browser-fallback rates;
- deckstring validity and deduplication;
- CN classification distribution;
- provenance coverage;
- actual and unattributed Scrape.do cost;
- per-site latest state and last-good time.

## Verification boundary

CI is offline. Fixtures cover valid/invalid/multiple deckstrings, 20-code compilations, Chinese statistics, lineage, 30/29/28/26-card similarity, classifier boundaries, CAPTCHA/SPA/403/429/dead URLs, Scrape.do escalation, secret-safe diagnostics, Koloda API normalization, Bilibili timestamp evidence, query generation, and score weights.

Live source layouts and provider behavior can drift. A live contract check is operational evidence, not a deterministic CI gate. If a site profile fails content validation, report that source as partial or blocked and cap downstream confidence.
