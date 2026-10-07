# ADR-004 — Evidence, status, and rule model

**Status:** accepted (v0.1.0)

## Decision

Every displayed value is a `PassportField`:

```
value, status, evidence[], rule, quality_flags[],
temporal, alternatives[], searched_sources[], explanation
```

Six public states only: `reported | derived | inferred |
not_found | not_applicable | conflict`. `status` is epistemology;
`quality_flags` is source-quality diagnostics — never substitutes.

- `reported` requires ≥1 `EvidenceRef` (provider, dataset,
  record_id, artifact/locator, retrieved/published/effective
  timestamps, raw_value, parser_version, transformations).
- `derived` requires evidence + versioned `RuleRef`.
- `inferred` requires evidence + rule + human-readable
  `explanation` with limitations.
- `conflict` requires ≥2 incompatible assertions; no silent winner
  unless a field policy says otherwise — and then the loser stays
  visible in `alternatives`.
- `not_found` requires `searched_sources` naming what was queried.
- `not_applicable` requires a rule explaining why the field does
  not apply (e.g. maturity on an equity).

Deterministic only: no probabilities, no LLM in the core.

## Rationale

"Unknown is a valid result" and "an unsupported assertion is a
bug" need machine-checkable form. The assertion validator
(`services/validate.py`) walks every materialized passport and
enforces the requirements above — `unsupported_assertions = 0`
is a release gate, not a convention.
