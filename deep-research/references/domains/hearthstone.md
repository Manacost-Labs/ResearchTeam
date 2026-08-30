# Hearthstone Domain Adapter

For Chinese server, deck, guide, or community intelligence, also load [Chinese Hearthstone intelligence](../chinese-hearthstone.md). Its classifications and deck comparisons are ingestion signals, not substitutes for current-patch authority, independent evidence, or the normal claim audit.

Load with the gaming adapter for Hearthstone research. This file adds Hearthstone-specific routing only.

## Context record

Before evidence collection, determine:

- mode: Standard, Wild, Twist, Arena, Battlegrounds, or another explicit mode;
- current patch and effective hotfixes;
- season and expansion/set context;
- region and rank/MMR bracket when statistics or strategy matter;
- entity identity: card, minion, hero, hero power, tribe/minion type, Tavern Tier, Dark Gift, Trinket/accessory, quest, anomaly, spell, or interaction;
- whether the question concerns rules, pool generation, economy, combat, scaling, leveling, synergy, meta, or player behavior.

Never move evidence between constructed and Battlegrounds, or between patches, without an explicit compatibility argument.

### Disambiguate “pool”

In Hearthstone, “pool” is overloaded. Before searching, split the applicable meanings, for example:

- offer-eligibility pool: which entities can be offered under turn, tier, tribe, text, hero, lobby, and prior-action constraints;
- finite shared-copy pool: whether obtaining an entity consumes one of the Tavern's limited copies;
- generation pool: which entities may be created outside the Tavern;
- active content pool: which cards, heroes, tribes, or systems are enabled in the current patch.

Evidence about one pool does not establish another. If official rules document eligibility but not copy depletion, keep the latter unresolved or validate it with a current controlled test.

## Research flow

```text
Question
  -> mode
  -> patch and season
  -> mechanic/entity identity
  -> official data
  -> current statistics
  -> high-MMR/expert analysis
  -> community patterns
  -> synergies and counterexamples
  -> evidence matrix and conclusion
```

## Source routing

### Mechanics and rules

1. Blizzard official pages, patch notes, support/rules text, or first-party game data;
2. reliable datamining and reproducible current-patch testing;
3. qualified expert demonstrations;
4. community testing.

### Meta

Use large current statistics plus current high-MMR interpretation. Candidate services may include HSGuru, HSReplay, Firestone, or other transparent current datasets. Their presence in this list is not an endorsement: inspect methodology, filters, sample, access limits, and patch window for each claim.

### Edge interactions

Seek official wording plus reproducible testing or video evidence. Record exact board state, entity text, order of operations, patch, and whether the result may be a bug.

### Strategy

Combine current statistics, elite players, and bounded community consensus. Useful discovery venues may include Blizzard, `/r/BobsTavern`, Hearthstone subreddits, YouTube, X, tournament/VOD material, and specialist communities. Open and inspect the actual material.

If public decision-level statistics are unavailable, say so and cap the result at a conditional heuristic unless strong independent expert evidence supports more. Do not treat end-board composition, popularity, or isolated high-roll screenshots as evidence for the optimal decision path.

## Battlegrounds and Dark Gifts tree

For Dark Gifts research, consider applicable branches:

- official mechanic and pool generation;
- charges, timing, discover/pool rules, and Tavern Tier dependency;
- first, second, and later use separately;
- immediate tempo versus holding value;
- economy, combat survival, leveling curves, scaling, and cap/floor effects;
- heroes, tribes/minion types, cards/minions, spells, synergies, Trinkets/accessories, quests/anomalies when active;
- high-MMR practices and rank dependence;
- statistical evidence and selection bias;
- common mistakes, failure modes, and counterexamples;
- patch/season changes that alter any branch.

Do not assume every branch is active in the current season; verify terminology and availability first.

## Frequent failure modes

- mixing Standard cards with Battlegrounds entities of the same name;
- using current-looking pages whose embedded stats cross a balance patch;
- treating top-lobby practice as universal ladder advice;
- interpreting end-board composition data as a successful build path without survivorship caveats;
- using a creator's old video after a pool, armor, damage, cost, tier, or text change;
- treating localization differences as separate mechanics;
- assuming a community term maps exactly to Blizzard's official term.

## Current-patch-only modifier

Exclude stale strategy and statistics. Older official mechanics may be `VERSION-COMPATIBLE` only after checking every relevant rule, tier, cost, pool, and timing dependency against the current patch.
