# Community Intelligence

## Boundary

Reddit, X, YouTube, forums, reviews, and chat communities are useful for discovering practices, edge cases, language, hypotheses, and expert reasoning. They are not automatically representative samples.

Never write “Reddit thinks X” from one thread or “the community agrees” from high engagement.

## Collection

For every material community item, record:

- platform, URL, author/channel, date, and relevant version;
- thread or video context;
- claim and reasoning, not only conclusion;
- expertise signal when observable;
- whether the mention is independent or reacting to the same upstream event;
- supporting examples and counterarguments;
- engagement only as context, never as proof of truth or prevalence.

Use built-in ChatGPT Search/Web to locate and open the actual post, thread, or video page. When available, use the read-only RedditAPI and GetXAPI routes defined in [optional source providers](source-providers.md) to obtain direct Reddit/X records, timestamps, context, and visible engagement without flattening the platforms together. For YouTube, inspect the relevant segment and record timestamps when possible. If access is partial, label it.

Provider ranking is not community prevalence. Segment automated posts, giveaways, stickied material, crossposts, replies, and incomplete comment trees before interpreting a sample. Preserve the exact subreddit or X query, time window, sort/product, cursor, provider position, and collection time.

## Expert detection for gaming and practitioner topics

Distinguish:

- casual user;
- high-rank or high-MMR player with verifiable current context;
- tournament player;
- content creator;
- developer or responsible official;
- theorycrafter or reproducible tester;
- statistical analyst or data provider.

Follower count is not sufficient expertise. Prefer current demonstrated performance, attributable professional role, methodological transparency, reproducible work, and topic-specific track record. A developer may be authoritative on mechanics but not necessarily optimal strategy; a top player may be authoritative on high-rank practice but not population-wide prevalence.

## Synthesis categories

- `strong`: broad, repeated, independent cross-source agreement with little serious counterevidence;
- `moderate`: several independent sources converge, but coverage or representation is limited;
- `contested`: credible arguments or practice patterns exist on both sides;
- `weak`: sparse or dependent repetition;
- `anecdotal`: isolated observation that generates a hypothesis only.

Use “minority opinion” as a position label inside a contested or weak field, not as a precise population estimate unless sampling supports it.

## Analysis

Cluster posts by atomic community claim. Track platforms, independent mentions, expert support, counterarguments, and version. Explain likely reasons for disagreement, such as rank, patch, mode, skill, incentives, or visibility bias.

When community views differ from statistics, present both and investigate metric mismatch, lag, accessibility, conditional expertise, sampling, or survivorship. Do not optimize for agreement.

## Language

Prefer bounded formulations:

- “Among the discussions reviewed...”
- “Several independent high-rank sources...”
- “The accessible Reddit and YouTube sample leaned toward...”
- “This was an anecdotal signal, not measured prevalence.”

Report inaccessible or under-covered platforms as limitations.
