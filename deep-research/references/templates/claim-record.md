# Claim Record Template

```yaml
claim_id:
claim:
claim_class: official_fact | statistical | strategic | causal | prevalence | superlative | forecast | interpretation
importance: critical | material | supporting | contextual

scope:
  population:
  geography:
  mode_or_platform:
  time_window:
  version_patch_season:
  conditions: []

evidence_required: []
supporting_evidence_ids: []
challenging_evidence_ids: []
source_lineages: []

status: supported | supported_with_conditions | contested | unsupported | unresolved | rejected
confidence: VERY_HIGH | HIGH | MEDIUM | LOW | SPECULATIVE
confidence_reason:

inference_steps: []
exceptions: []
unknowns: []
wording_for_output:
```

If one field contains two independently falsifiable assertions, split the record.
