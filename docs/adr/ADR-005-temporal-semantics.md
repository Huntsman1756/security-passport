# ADR-005 — Temporal semantics: honest bases, no fake symmetry

**Status:** accepted (v0.1.0)

## Decision

Every temporal claim carries:

```yaml
temporal:
  basis: native_history | reconstructed | observed_history | current_only
  coverage_start: <date|null>
  coverage_end: <date|null>      # null = open-ended
  left_censored: <bool>
  source_time_semantics: provider_publication_time | effective_time | retrieval_time
```

Per-block bases in v0.1.0:

- IDENTITY — `reconstructed` via OpenInstrument (FIRDS
  publication-time, left-censored before the upstream baseline).
- SECONDARY MARKET — same basis; sentinels normalized at our
  projection layer, raw preserved.
- PRIMARY MARKET — `observed_history` from T0 (PRIII has no public
  history surface; we archive every retrieval).
- POST-TRADE — `observed_history` (ECB SSS/links pages carry a
  "Last updated" stamp; we archive each observation).
- EUROSYSTEM COLLATERAL — `current_only` in v0.1.0 (single
  snapshot per update run); the store is ready for native history
  when multiple snapshots are ingested.

`--as-of` is **not** public in v0.1.0 — the storage layout is
temporal from day one, but a historical passport requires
per-block coverage honesty that is scheduled for v0.2.

## Rationale

Mixing publication time, effective time, and retrieval time is the
most common way reference-data systems lie. We name the semantics
on every field instead.
