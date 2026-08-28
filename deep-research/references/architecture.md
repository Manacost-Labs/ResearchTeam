# Architecture

## Decision

Use a progressive-disclosure Skill package rather than the requested flat tree. `SKILL.md` remains the orchestration layer; substantial shared rules live in `references/`; domain overlays, reusable records, and examples are nested by purpose. `agents/openai.yaml` supplies ChatGPT Work metadata. This minimizes default context while keeping every module directly discoverable from the entrypoint.

## Runtime flow

```text
User query
  -> Query interpreter
  -> Research planner and recursive tree
  -> optional persistent research-run bundle
  -> ChatGPT Search/Web
       -> primary sources
       -> statistics
       -> experts
       -> community
  -> Evidence collector
  -> Atomic claim extraction
  -> Evidence matrix
  -> Contradiction search
  -> Freshness/version validation
  -> Adversarial Research Auditor
  -> Research database
  -> deterministic integrity validation
  -> Final research report
```

ChatGPT Search/Web is the built-in discovery and source-access layer. Search snippets are never promoted directly into the evidence database. The collector relies on the content of opened sources and records access limitations.

## Layers and responsibilities

| Layer | Owns | Does not own |
|---|---|---|
| `SKILL.md` | activation, depth, routing, phase order, completion | detailed domain/source rules |
| shared protocols | search, provenance, verification, freshness, confidence, audit | domain-specific entities |
| domain adapters | source preferences, version axes, terminology, failure modes | duplicated core methodology |
| templates | working artifact schemas | mandatory final prose layout for every request |
| research-run scripts | reproducible bundle initialization and referential-integrity validation | judging factual truth |
| validation | packaging audit and simulated acceptance evidence | runtime research |

## Artifact flow

1. The research plan fixes meaning and scope.
2. The query plan maps question-tree leaves to search families.
3. Source records preserve provenance and source-level metadata.
4. Evidence records capture exact support or challenge.
5. Claim records create falsifiable units.
6. The matrix tests authority, independence, contradictions, and confidence.
7. Community and contradiction reports preserve disagreement instead of flattening it.
8. The audit controls whether synthesis is allowed.
9. The final or raw template exposes validated findings for a user or downstream Writer Skill.

## Key engineering choices

- Source ranges guide effort but never define completion; branch saturation and quality gates do.
- Confidence is claim-level and categorical, because a single report-level score hides weak subclaims.
- “Research Auditor” is a role contract inside the workflow, not an assumed separate agent. The Skill works in environments without subagent support.
- Domain adapters refine claim authority and freshness without weakening universal evidence rules.
- Templates are Markdown working records so they remain tool-agnostic and can be used in chat or persisted as files.
- The package has no external runtime dependency. Built-in ChatGPT Search/Web supplies network research.
- File-backed runs are optional. They are required only when persistence, resumability, raw evidence delivery, or cross-Skill handoff materially improves the task.
- Deterministic validators prove structure and provenance links, not whether a source is true; the Research Auditor retains that semantic responsibility.

## Extension rules

- Add a domain adapter only when source authority, version semantics, or validation failure modes genuinely differ.
- Add a protocol only when it has a distinct decision boundary and conditional load value.
- Keep each rule in one authoritative file; link rather than copy.
- Do not encode a one-off research finding as universal methodology.
- Preserve the invariant: validation and audit precede strong synthesis.
