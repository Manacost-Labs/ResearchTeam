# Search Strategy

## Tool contract

Use the built-in ChatGPT Search/Web capability as the default for internet research. Use Search to discover candidates and Web/open-page access to inspect sources. When a branch requires direct Reddit/X access, TranscriptAPI YouTube search/transcripts, or TinyFish extraction, apply [optional source providers](source-providers.md) without changing this evidence boundary. Search-result text, snippets, answer cards, provider search results, and AI summaries are discovery metadata, not verified evidence.

Prefer opening the original URL. If the original is unavailable, try its official mirror or archive, then seek independent confirmation. Record unresolved access limitations and lower confidence when the missing source matters.

## Search from research-tree leaves

For every material leaf, create a query set from the applicable families:

| Family | Purpose | Query patterns |
|---|---|---|
| general | map terminology and candidate sources | `[topic] strategy`, `[topic] explained` |
| primary | locate original rules or statements | `[topic] official`, `[topic] documentation`, `[topic] patch notes` |
| statistics | locate datasets and measurements | `[topic] statistics`, `[topic] winrate`, `[topic] data`, `[metric] methodology` |
| experts | find attributable analysis | `[topic] expert`, `[topic] high rank`, `[topic] guide`, `[expert name] [topic]` |
| Reddit/forums | sample community reasoning | `site:reddit.com [topic]`, `[topic] forum discussion` |
| X/social | find current statements and debate | `[topic] [author]`, `[topic] discussion`, `site:x.com [topic]` |
| YouTube | locate demonstrations and long-form analysis | `[game] [patch] [topic] guide`, `[verified player] [topic]`, `[topic] tournament VOD`, `[topic] coaching`, `[topic] mistakes` |
| mistakes | expose failure modes | `[topic] mistakes`, `[topic] avoid`, `[topic] common error` |
| synergies | find interaction effects | `[topic] synergy`, `[topic] interaction`, `[A] [B] interaction` |
| counterargument | challenge the leading hypothesis | `[topic] overrated`, `[topic] weak`, `why not [claim]`, `[claim] wrong` |
| freshness | anchor version and date | `[topic] [current year]`, `[topic] [patch]`, `[topic] [season/version]` |

Patterns are prompts for expansion, not literal mandatory queries.

## Evidence-availability gate

Before spending most of the search budget, test whether each required evidence class is actually accessible:

1. run at least two materially different targeted queries for the class when it is decision-critical;
2. try the likely primary owner or named database directly;
3. record `AVAILABLE`, `PARTIAL`, `BLOCKED`, or `NOT FOUND`, including paywalls, login requirements, missing filters, and version mismatch;
4. state how the result changes the research claim.

If decision-level statistics are not found, do not infer an optimum from popularity, final-board data, or community repetition. Deliver a conditional heuristic, a narrower descriptive conclusion, or an unresolved gap. Continue searching only when a new source family, vocabulary, access route, or version marker makes the next query materially different.

## Query expansion

Expand the user's words into:

- synonyms and antonyms;
- official and community terminology;
- alternative, previous, and localized names;
- English-language equivalents when the user asks in another language;
- mechanics, entities, authors, datasets, and products connected to the concept;
- current year, version, patch, season, expansion, jurisdiction, or population;
- pro and con formulations.

Example question: `When should I use the first Dark Gift?`

Possible expansions:

- `Dark Gift first use`
- `best timing Dark Gift`
- `should I save Dark Gift`
- `Dark Gift Tavern Tier`
- `Dark Gift early game`
- `Dark Gift high MMR`
- `Dark Gift strategy Reddit`
- `Dark Gift first charge guide`
- `why save Dark Gift`
- `Dark Gift mistakes`

## Pass discipline

1. Broad discovery identifies vocabulary, primary owners, datasets, experts, and disagreement.
2. Targeted collection opens the strongest candidates per branch.
3. Gap search uses only the latest gap list.
4. Contradiction search negates or reframes preliminary claims.
5. Freshness search tests change events and current applicability.
6. Audit search resolves only failed gates.

Do not repeat equivalent queries unless a new date/version, source family, language, or disconfirming frame makes them materially different.

## Coverage log

For deep or exhaustive research, track each material branch with:

- query families attempted;
- useful and rejected source IDs;
- source classes still missing;
- access failures;
- last new claim or counterargument;
- saturation status.

The log prevents high-volume searching in one easy branch from hiding untouched branches.

## Special media handling

- For X, Reddit, and forums, open the actual post or thread where possible and preserve author, timestamp, thread context, and edit/deletion risk.
- For YouTube, verify the page date and author/channel identity, inspect the relevant transcript/video segment, and record a timestamp; a title, thumbnail, view count, or search position is not evidence.
- For PDFs, inspect the exact page or table and verify surrounding definitions.
- For live pages, record access date and version markers because content may change.
