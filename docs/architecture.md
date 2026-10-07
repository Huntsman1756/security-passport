# Architecture

Security Passport is a **read model** over two layers: the
OpenInstrument security master (upstream, unchanged) and a small
set of own-source stores it maintains itself. It never mutates
source systems, never infers settlement paths, and renders
`Unknown` when evidence is absent.

```text
official sources                OpenInstrument (upstream, read-only)
┌─────────────────────┐         ┌──────────────────────────┐
│ ECB eligible assets │         │ canonical instruments /   │
│ ECB SSS & links     │         │ listings / identifiers /  │
│ ESMA PRIII          │         │ issuer / evidence API     │
│ ISO 10383 MIC       │         └───────────┬──────────────┘
└──────────┬──────────┘                     │ InstrumentProvider
           │ own-source ingestion           │ (fixture in tests)
           ▼                                │
┌──────────────────────────────┐            │
│ data/raw/generation-XXXX/    │            │
│ data/read/generation-XXXX/   │ ◄──────────┘
│ CURRENT → generation-XXXX    │   PassportStore
└──────────┬───────────────────┘
           │   pinned per request
           ▼
┌──────────────────────────────┐
│ PassportBuilder              │  field-level statuses, rules,
│ (adjudication + rule engine) │  evidence refs, conflicts
└──────────┬───────────────────┘
           ▼
   Passport JSON (schema_version 1)
   ├── CLI (typer)
   ├── REST (FastAPI, read-only)
   └── SPA (React) — renders the same JSON
```

## Key boundaries

| Layer | Does | Never does |
|---|---|---|
| InstrumentProvider | expose upstream facts | normalize sentinels, resolve conflicts |
| PassportStore | own-source rows keyed by ISIN | instrument resolution, scoring |
| Builder | map facts → typed fields, apply rules | guess defaults, fuzzy match, LLM calls |
| API/CLI | serialize the passport JSON | rebuild logic, cross-request caching |
| SPA | render the passport JSON | derive anything the API didn't say |

## Generations

`data/read/generation-XXXX/` contains immutable per-source
stores (`ecb_eligible_assets`, `ecb_sss_links`, `mic`, `priii`),
each with a `meta.json`. `manifest.json` carries the file
inventory (sha256 each), parser/adjudicator versions, provider
metadata, and a `semantic_fingerprint` (volatile fields stripped)
— an identical rebuild fingerprints identically. Publication is an
atomic `CURRENT` pointer swap; readers pin `CURRENT` once at
process start and rebuild on reload. No serving reads ever
touch `data/staging/`.

## Failure posture

- Schema drift → `SchemaError` → ingest aborts → `CURRENT` unchanged.
- Provider unreachable → field `not_found` with `searched_sources`,
  never an invented default.
- Missing generation → `503 DATASET_NOT_READY` (API),
  degraded `health/ready`.
- Upstream conflict exported without candidates → field
  `conflict` with the upstream state preserved as evidence.
