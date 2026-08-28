# Output Policy

## Boundary

The Skill produces a research report or raw evidence database. It does not automatically turn research into an SEO article, guide, news story, or polished editorial draft. Preserve material findings that a downstream Writer Skill may need.

## Normal research report

Use the sections that improve the answer:

1. Research Topic
2. Executive Summary
3. Scope
4. Current Context
5. Research Questions
6. Key Findings
7. Detailed Findings
8. Evidence
9. Statistics
10. Expert Opinions
11. Community Intelligence
12. Contradictions
13. Exceptions
14. Unknowns
15. Confidence
16. Sources

Do not print empty sections. Lead with the answer and as-of context. Keep citations adjacent to significant claims and link directly to original inspected sources.

## Raw research mode

Use the raw template for exhaustive writer-ready material. Preserve each finding's claim, significance, primary and supporting evidence, community evidence, counterarguments, patch/version relevance, confidence, limitations, and notes for the writer. Include useful negative findings and unresolved gaps.

For a persistent run, deliver the validated bundle plus the [handoff template](templates/handoff.md). The handoff must state `ready`, `ready_with_warnings`, or `not_ready`; do not infer readiness from prose quality.

## Evidence visibility

The full evidence matrix is internal by default. Show it when the user requests raw research, an audit trail, a fact-check dossier, or claim-level provenance. In a concise answer, surface only evidence necessary to verify key findings and explain uncertainty.

## Citation behavior

- Cite every significant externally verifiable claim.
- Prefer the original page, dataset, official document, or actual post/video.
- Do not cite a ChatGPT Search result page, snippet, or AI summary as evidence.
- Never cite a source that was not opened and checked for the attached claim.
- Preserve directness: one citation should not appear to support a paragraph of unrelated assertions.

## Bounded completeness language

Avoid “I researched everything,” “complete consensus,” or similar unprovable claims. Prefer:

- “Among the sources reviewed...”
- “Across the accessible sources...”
- “Several independent discussions...”
- “Available current-patch data indicates...”

## Uncertainty

Put limitations next to affected findings when possible, then summarize them in `Unknowns`. State what is unknown, why, and whether it could change the answer.

## Failure output

If the audit remains `fail`, deliver an incomplete research note rather than a confident answer. Identify the failed claims, missing evidence, attempted coverage, and the safest bounded conclusion, if any.

For a file-backed run, a failed final bundle validator also blocks `ready` status. Structural integrity does not prove factual truth, but broken provenance makes professional handoff unsafe.
