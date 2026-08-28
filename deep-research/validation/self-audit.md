# Architecture Self-Audit

## Status

`pass`

## Audit scope

- activation and default-mode behavior;
- progressive-disclosure routing;
- ChatGPT Search/Web boundary;
- claim-to-evidence traceability;
- source independence and freshness;
- statistics and community handling;
- contradiction search and confidence;
- completion, saturation, and failure behavior;
- separation of research from writing;
- untrusted web-content handling and data minimization;
- persistent-run reproducibility and referential integrity;
- package links, metadata, and scaffold residue.

## Issues found and resolved

| Issue | Risk | Resolution |
|---|---|---|
| Flat requested tree conflicted with current Skill progressive disclosure | unnecessary context loading | moved methods under `references/`, kept a concise orchestration entrypoint, documented the choice in architecture |
| Built-in web capability was implicit | the runtime might treat search snippets as evidence | explicitly named ChatGPT Search/Web in the entrypoint, architecture, search strategy, README, examples, and tests; required opening original sources |
| Default deep mode could conflict with narrow factual research | URL padding and wasted work | made source ranges non-binding and allowed one decisive primary source for a narrow fact; saturation controls stopping |
| Fixed source orientations could become completion quotas | fake completeness | made per-branch novelty and quality gates the completion test |
| Strategy claims and official facts have different burdens | over- or under-verification | added claim-dependent authority and verification rules |
| Multiple URLs could hide one evidence origin | false corroboration | added `lineage_id`, upstream-source fields, and independence checks |
| Old sources can be either valid or stale | date-only freshness errors | added current/source version comparison and six freshness statuses |
| Community repetition could be presented as consensus | prevalence overclaim | added independent-mention, platform, expertise, counterargument, and bounded-language requirements |
| “Auditor” could imply a required separate agent | runtime incompatibility | defined it as an adversarial role contract, not a deployment dependency |
| Exhaustive guide research could become article writing | loss of evidence and scope creep | added automatic raw-research routing for reusable guide/article bases and a hard research/writing boundary |
| A failed audit lacked safe output behavior | confident unsupported conclusion | `fail` now blocks confident synthesis and requires targeted search, claim reduction, or incomplete-report labeling |
| Web pages could contain instructions aimed at the researcher | prompt injection, secret disclosure, or unauthorized action | added an explicit untrusted-content boundary, safe-tool rules, secret minimization, and a Quality Gate check |
| Large research could not be resumed or handed off reproducibly | lost provenance and repeated discovery | added a persistent bundle with manifest, ledgers, checkpoints, stable IDs, lifecycle states, and handoff contract |
| A polished report could hide broken Claim → Evidence links | false professional readiness | added a deterministic final-stage validator and made its failure block `ready` status |
| Bundle initialization could overwrite user work | data loss | initializer refuses every non-empty target; integration test confirms preservation |
| “Pool” was treated as one Hearthstone mechanic | evidence for offer eligibility could be misapplied to finite-copy depletion | split offer, shared-copy, generation, and active-content pools before research |
| Statistics-heavy mode assumed public decision data would be found | community heuristics could be mislabeled as an optimum | added a bounded evidence-availability gate and mandatory confidence downgrade |
| Launch documentation could hide later partial patches | stale row values in a current guide | added chronological baseline-plus-overlay reconstruction and row-level provenance |
| Bundle timestamps were documented but not fully enforced | incomplete provenance could still validate | validator now checks query/source/checkpoint timestamps and checkpoint gap-list shapes |
| Release metrics could be self-reported | a polished result file could hide false traceability or missing fingerprints | release validation now recomputes metrics from each linked final bundle and rejects tampering |
| Long-running bundles lacked operator commands | resume/export behavior depended on memory and ad hoc packaging | added validated `resume`, `compare`, deterministic `export`, and gated `release` operations |

## Residual warnings

- The Skill cannot guarantee access to X, Reddit, YouTube, paywalled sources, deleted posts, or private datasets. Runtime must disclose missing coverage.
- Source-count orientations remain inherently topic-dependent; the text repeatedly marks them non-binding.
- Live sources remain mutable after the recorded access date; current claims must be re-run after relevant change events.
- Deterministic validation and semantic audit reduce but cannot mathematically prove source truth; human review remains appropriate for high-stakes release use.

## Verification evidence

- The package audit checks required artifacts, internal Markdown targets, matching Skill name, invocation metadata, and unfinished markers.
- The official Skill validator checks frontmatter and packaging.
- Twenty live ChatGPT Search/Web cases across five domains plus two adversarial fixtures exercise all seven required benchmark categories.
- Sixteen integration tests cover initialization, working/final validation, migration, fingerprints, semantic gold, benchmark tampering, deterministic export, timestamps, and overwrite protection.
- Release results are derived from linked schema 1.1 bundles; every mutable benchmark source is fingerprinted and every critical claim is traceable.

No critical contradiction remains between the source-count guidance and saturation rule, the one-primary-source rule and strategy corroboration rule, or the default deep mode and narrow factual execution.
