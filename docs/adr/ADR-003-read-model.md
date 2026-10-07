# ADR-003 — Parquet/DuckDB read model, query-time passport assembly

**Status:** accepted (v0.1.0)

## Decision

Own-source stores (ECB eligible assets, ECB SSS/links, PRIII
document graphs, MIC registry, Iberclear facts) are immutable
Parquet/JSONL inside dated generations:

```
data/
  raw/<provider>/<retrieved_date>/<sha256>      immutable evidence
  observations/<provider>.jsonl                 observed history
  read/generation-NNNN/                         published root
    stores/*.parquet
    manifest.json
  read/CURRENT
```

Passports are **assembled at query time** from the pinned
generation + pinned OpenInstrument generation, then cached by
`(generation, isin, schema_version)`. We do not materialize
passports for 3.4M ISINs.

## Rationale

- The passport is a projection; rebuilding it per request keeps the
  semantics in one place (the builder) and makes `--explain`
  trivially honest.
- Own-source stores are small (ECB ~31k rows, SSS ~dozens,
  MIC ~8k, PRIII observed corpus). DuckDB lookups are
  millisecond-range; the 300ms p95 target holds.
- Generations give atomic publish/rollback for free — the
  OpenInstrument-proven pattern, re-implemented at our scale.

## Consequences

- A passport never mixes generations: one request pins one
  `(passport_generation, openinstrument_generation)` pair.
- `not_found` means "searched the pinned generation" — the
  `searched_sources` list names what was consulted.
