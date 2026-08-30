# Simulated Acceptance Tests

These are routing and invariant simulations, not live factual Hearthstone research. No source, game fact, or conclusion is claimed from the simulations.

## Chinese Hearthstone ingestion

- A valid IYingdi fixture with `服务器：国服`, games, win rate, rank window, and one 30-card deck must validate and classify as `CN_META`.
- `本人构筑` plus a CN ladder result may classify as `CN_ORIGINAL` only after a completed western-match check finds no match.
- A 28/30 overlap with a western deck must classify as `CN_VARIANT` and preserve added/removed DBF IDs.
- A GamerSky repost with western attribution must preserve the original lineage and classify as `WESTERN_REPOST`, not independent evidence.
- A 17173 compilation containing twenty valid codes must return twenty source-to-deck relationships.
- CAPTCHA, login, SPA shell, 403, 429, dead URL, and provider-account failures must never be recorded as successful content.
- A Bilibili payload must preserve subtitle timestamps and produce structured evidence only for strategy-bearing segments.
- Configuration reports and all error/result envelopes must omit Scrape.do and Koloda API secret values.

## Test 1 — narrow factual research

### Prompt

`What exactly determines Dark Gift pool?`

### Activated configuration

- Mode: `deep` because no explicit depth was supplied; execution remains compact because the question has one factual mechanics branch.
- Type: fact-check + explanatory.
- Adapters: gaming + Hearthstone.
- Current context: Battlegrounds mode, current patch and season must be established before accepting rule evidence.
- Modules: research protocol, Search/Web strategy, source policy, evidence protocol, verification, freshness, confidence, quality gate, output policy.
- Community analysis: not required unless official rules are incomplete and community testing becomes evidence.

### Pipeline

1. Interpret “pool” and split candidate dimensions such as Tavern Tier, charge/timing, exclusions, and season-specific systems.
2. Use ChatGPT Search/Web to discover and open current Blizzard rules/patch notes and relevant first-party data.
3. If official text is incomplete, seek reproducible current-patch tests or datamining without promoting them to official fact.
4. Build atomic mechanics claims and verify version compatibility.
5. Challenge the preliminary rule with edge-case and changed-patch queries.
6. Audit semantic support, current patch, and any undocumented inference.

### Weakness discovered and correction

Risk: the default `deep` source orientation could be mistaken for a quota and inflate a narrow official fact. The protocol now states that depth does not change truth standards, source ranges are non-binding, and one decisive current primary source may establish a narrow fact. Saturation stops the branch once new quality sources add nothing material.

### Simulated result

`pass_with_warnings`: the route is correct; actual confidence depends on whether current official pool rules are explicit. The workflow must return an unresolved narrow point rather than infer it if primary and reproducible evidence are absent.

## Test 2 — strategic research

### Prompt

`When should the first Dark Gift be used?`

### Activated configuration

- Mode: default `deep`.
- Type: strategic + statistical + community intelligence.
- Adapters: gaming + Hearthstone.
- Conditional modules: freshness, contradiction search, community intelligence, confidence.
- Required context: current patch/season, MMR range, and the outcome behind “should” such as survival, average placement, top-four rate, or win rate.

### Pipeline

1. Split immediate use, intermediate-tier use, and holding for later; add economy, tempo, leveling, health, hero, lobby, and synergy conditions.
2. Discover current mechanics, datasets, high-MMR analyses, Reddit/forum discussions, YouTube explanations, and X statements with ChatGPT Search/Web.
3. Open sources and collect claim-sized statistics, expert reasoning, and bounded community patterns.
4. Check sample, timeframe, patch, MMR/rank, filters, decision-point availability, and survivorship/selection bias.
5. Search specifically for why the leading timing is bad or why another tier is better.
6. Build the evidence matrix and write only a conditional recommendation that survives audit.

### Weakness discovered and correction

Risk: “best timing” is undefined and could let the system optimize the wrong outcome. The research plan now requires operational definitions and success criteria before search. The Hearthstone adapter also separates tempo/survival, economy, leveling, placement metrics, and lobby/MMR conditions.

Risk: multiple creator posts may repeat one dataset. Source records now include `lineage_id`, and verification separates independent measurement from independent interpretation.

### Simulated result

`pass`: all required evidence streams, contradiction search, version controls, and conditional wording are routed. A universal answer would fail the superlative/strategy gates unless comparative evidence justified it.

## Test 3 — exhaustive guide research

### Prompt

`Research everything needed for a complete Dark Gifts guide.`

### Activated configuration

- Mode: inferred `exhaustive` because the request demands comprehensive guide research.
- Modifier: inferred `raw-research` because the requested deliverable is a reusable base for a downstream guide; this does not generate the guide itself.
- Operations: persistent research bundle with stable IDs, pass checkpoints, final integrity validation, and Writer handoff.
- Type: factual mechanics + statistical + strategic + expert + community intelligence + fact-check.
- Adapters: gaming + Hearthstone.
- Modules: all core and conditional protocols.

### Pipeline

1. Build a recursive tree covering mechanics, pool generation, charges/timing, economy, combat, scaling, leveling curves, heroes, tribes/minion types, cards/minions, synergies, season systems, mistakes, community positions, statistics, counterexamples, and patch history.
2. Execute discovery, deep collection, gap, contradiction, freshness, and audit passes; add more targeted passes only for named gaps.
3. Maintain branch coverage, source lineage, claim/evidence records, community position maps, and contradiction reports.
4. Test saturation separately for every major branch. Source count cannot compensate for an untouched branch.
5. Run the adversarial Auditor and preserve rejected, contested, and unresolved claims in raw output.
6. Validate the completed bundle and mark the handoff `ready`, `ready_with_warnings`, or `not_ready` from audit and integrity results.

### Weakness discovered and correction

Risk: “complete” could cause endless searching or false completeness. The protocol now uses per-branch saturation plus bounded language and forbids “I studied everything.”

Risk: a fixed 50–150 target could reward URL padding. The range is explicitly orientation only; evidence quality, independence, branch coverage, and material novelty control completion.

Risk: the auditor could be interpreted as requiring a separate subagent. Architecture now defines it as a role contract usable in a single-agent environment.

Risk: research could silently become an SEO guide. Output policy and automatic `raw-research` routing preserve an evidence database for a separate Writer Skill.

### Simulated result

`pass`: the exhaustive route covers recursive planning, multi-pass research, gaps, community, statistics, contradictions, freshness, saturation, audit, and writer-ready raw output without claiming factual completion before live research.

## Acceptance summary

| Requirement | Test 1 | Test 2 | Test 3 |
|---|---:|---:|---:|
| primary mechanics | yes | yes | yes |
| current version/patch | yes | yes | yes |
| statistics context | conditional | yes | yes |
| experts/community | fallback only | yes | yes |
| contradiction search | yes | yes | yes |
| recursive tree | bounded | yes | yes |
| gap detection | yes | yes | yes |
| saturation | branch | branch | all major branches |
| adversarial audit | yes | yes | yes |
| raw writer-ready output | no | optional | yes |

All three simulations preserve the invariant that Search/Web discovery precedes inspected evidence, and validated evidence precedes strong synthesis.
