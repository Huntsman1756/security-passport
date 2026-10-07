# REST API — `schema_version: 1`

Read-only. `schema_version` is bumped on breaking contract changes.

## `GET /api/v1/passports/{isin}`

Returns the passport JSON. Status: `200` (found, partial, or
unknown — all are valid passports), `422 INVALID_ISIN`,
`503 SOURCE_UNAVAILABLE | DATASET_NOT_READY`.

Headers: `ETag` (semantic — generation + upstream generation +
ISIN), `Cache-Control: public, max-age=60`.

## `GET /api/v1/passports/{isin}/evidence`

Flattened evidence ledger for the whole passport —
`{block, field, provider, dataset, record_id, artifact_id,
retrieved_at, raw_value, …}`.

## `GET /api/v1/passports/{isin}/sources`

`source_summary` + union of `searched_sources` actually checked
for this ISIN.

## `GET /api/v1/search?q=`

`exact_isin` or `text_candidates` — candidate list only, never a
resolved decision.

## `GET /api/v1/status`

Service version, provider mode, pinned generation, upstream
generation, provider/store errors, attribution notice.

## `GET /health/live` · `GET /health/ready`

Liveness is binary; readiness checks that the store actually
answers a lookup (`{"checks": {"provider", "store"}}`).

## Error shape

```json
{"error": {"code": "INVALID_ISIN", "message": "…",
           "details": null, "request_id": "abc123"}}
```

Codes: `INVALID_ISIN`, `NOT_FOUND` (route), `PARTIAL_DATA`,
`SOURCE_UNAVAILABLE`, `DATASET_NOT_READY`,
`INTERNAL_DATA_INTEGRITY_ERROR`.

## Guarantees

- One request = one pinned `(generation, upstream_generation)` pair.
- A fallen source degrades to field-level `not_found`, never a
  fabricated value, never a 500.
- The SPA renders only what this API returns; JSON and UI are
  semantically identical.
