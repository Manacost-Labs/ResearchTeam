# Research Protocol

## Phase contract

Every phase produces an inspectable artifact or an explicit “not applicable” reason.

### A. Interpret

Normalize the request into the `MAIN QUESTION`, intended use, ambiguous-term definitions, time, geography, population, platform or mode, patch/season/version, included and excluded scope, depth, and output mode. Define the metric behind “best,” “common,” “meta,” “effective,” or “safe” before searching. When one term names multiple mechanisms or data structures, create a separate branch for each meaning and state which meaning the final answer covers.

### B. Plan

Build a recursive tree whose leaves are answerable questions. Split a leaf when it combines mechanisms, outcomes, populations, time periods, modes, or evidence types. Annotate each material leaf with why it matters, evidence required, preferred source class, freshness constraint, and likely confounders.

Prioritize branches by effect on the final answer, not ease of search.

### C. Discover with ChatGPT Search/Web

Pass 1 maps vocabulary, primary-source owners, datasets, named experts, community venues, and likely controversies. Follow citation chains toward original evidence. A result card or snippet is only a lead.

Before deep collection, run a bounded evidence-availability gate for every evidence class required by the plan. Record `AVAILABLE`, `PARTIAL`, `BLOCKED`, or `NOT FOUND`, the queries tried, and the consequence for claim strength. Missing public statistics or expert evidence changes the permitted conclusion; it does not authorize substituting community anecdotes under the same label.

### D. Gather deep evidence

Pass 2 opens candidate sources and collects claim-sized evidence. Discard or downgrade irrelevant, opaque, undated-when-date-matters, version-mismatched, content-farm, or unverifiable derivative sources. Do not discard disagreement merely because it is inconvenient.

### E. Detect gaps

After each major pass record:

- `WHAT WE KNOW`: validated or strongly supported;
- `WHAT WE THINK`: plausible inference needing more support;
- `WHAT IS CONTESTED`: material competing claims;
- `WHAT WE DON'T KNOW`: unanswered scope;
- `WHAT NEEDS MORE EVIDENCE`: actionable search gaps.

Pass 3 searches only those gaps.

### F. Model and validate claims

Create atomic claims and mark each descriptive, causal, predictive, normative, strategic, superlative, or prevalence. Validate semantic support, authority for the claim type, independence, freshness, scope match, and statistical context.

### G. Challenge and refresh

Pass 4 searches for the strongest plausible contradiction to the preliminary conclusion. Pass 5 verifies current version, patch, season, date, and any change events that could invalidate earlier evidence.

### H. Audit

Pass 6 runs the adversarial quality audit. For each failure:

1. run a gap-targeted search;
2. narrow, qualify, or remove the claim; or
3. leave it explicitly unresolved and explain its impact.

### I. Synthesize

Only after validation and audit, answer at the supported level of certainty. Separate established facts, statistics, expert interpretations, community patterns, counterarguments, and unknowns.

## Depth modes

Depth changes breadth and recursion, not truth standards.

| Mode | Behavior | Source/evidence orientation |
|---|---|---|
| quick | bounded tree; decision-critical branches; six passes may be compact | roughly 10–20 strong items when warranted |
| deep | default; recursive material branches and mixed source types | roughly 30–60 useful items when warranted |
| exhaustive | explicit coverage map, edge cases, unresolved log, further passes | roughly 50–150+ when topic breadth justifies it |

Never pad the dossier to meet a range. A primary fact can be resolved with one decisive source; a broad guide can require many evidence items from fewer URLs.

## Modifiers

- `community-heavy`: broaden platforms and consensus segmentation; never lower evidence standards.
- `statistics-heavy`: prioritize datasets, definitions, methods, and sensitivity checks.
- `primary-sources-only`: exclude secondary support from conclusions; report lost coverage.
- `current-patch-only`: exclude incompatible evidence; permit older version-compatible mechanics only when explicitly justified.
- `raw-research`: preserve rich claim records and notes for a downstream writer.
- `fact-check`: foreground verdict criteria and exact semantic support.
- `contradiction-heavy`: expand alternative hypotheses and disconfirming queries.

## Saturation

A branch is saturated when several consecutive new quality sources add no new claim, counterargument, confidence change, relevant subcategory, or source lineage. Check major branches independently. Saturation is invalid if a required source class was never searched, current-version evidence is missing, or access failures hide a material channel.

## Completion

Finish when all decision-relevant branches are answered, excluded, or unresolved with impact stated; central claims have inspected evidence appropriate to their type; dependencies and contradictions are accounted for; freshness requirements are satisfied or disclosed; major branches are saturated; and the audit is `pass` or `pass_with_warnings`.

Source count, elapsed time, or polished prose alone never proves completion.
