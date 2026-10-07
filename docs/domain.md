# Domain model

## Field statuses

| Status | Meaning | Contract |
|---|---|---|
| `reported` | A source stated this verbatim (possibly through a versioned adapter). | ≥1 evidence |
| `derived` | Mechanical application of a versioned rule to reported data. | evidence + rule |
| `inferred` | Builder synthesis combining sources or applying a domain heuristic. | evidence + rule + explanation |
| `conflict` | Sources disagree. | ≥2 alternatives **or** reported upstream conflict state (evidence + explanation) |
| `not_found` | Checked; nothing found. | `searched_sources` non-empty |
| `not_applicable` | The concept does not apply to this instrument class. | rule |

Every field additionally carries `evidence[]`, `alternatives[]`,
`quality_flags[]`, `temporal`, and optional `raw_value`/`unit`.

## Distinctions that are never collapsed

- **Fact vs evidence vs inference** — the field's *value* is the
  fact; `evidence` is what supports it; `rule`/`explanation` is
  how inference happened.
- **Unknown vs false** — absence in a non-enumerative source is
  `not_found`, never `false`.
- **Instrument vs listing vs admission** — an instrument exists;
  an ISIN is listed on venues; admission is a listing attribute.
- **Issuer vs management company** — FIRDS field 5 is
  "issuer or operator of the trading venue"; the role qualifier is
  carried, not relabelled.
- **Issuer SSS vs investor SSS** — ECB reports the issuer-side
  code; generic link topology is context, never a settlement path.
- **Current vs historical** — `snapshot`, `provider_publication`,
  `observed`, and `derived` time semantics are explicit per field;
  reconstructed FIRDS history is left-censored.

## Quality flags

`source_default_value` (FIRDS `9999-12-31` sentinel surfaced as
`None` with the raw preserved), `possible_source_default`,
`provider_conflict_state`, `stale_source`, `partial_coverage`,
`historical_gap`, `not_enumerated`, `approximate`,
`external_unverified`.

## Rules

Rules live in `security_passport.domain.rules` — versioned,
append-only (`rule_id`, `rule_version`, `inputs`, `basis`,
`limitations`). Any `derived`/`inferred`/`not_applicable` field
must reference a registered rule; `ref()` fails closed on unknown
ids. Current rules: `instrument_type`, `dated_instrument_scope`,
`venue_state`, `first_admission`, `eurosystem_eligibility`,
`settlement_path`, `issuer_lei_adjudication`, `entity_role`,
`haircut_display`.

## POST-TRADE model (v0.1.2)

Four separate assertions that must never merge:

| concept | field/collection | semantics |
|---|---|---|
| issuer CSD | `issuer_csd` (field) | ECB `ISSUER_CSD` — collateral-reference semantics, `scope: eurosystem_collateral_reference`. Only valid in the ECB dataset's own sense. |
| settlement locations | `settlement_locations` (collection) | Instrument-level CSD admission — a CSD-published file listing this ISIN. Multi-valued: `issuer_csd` / `current_place_of_settlement` / `designated_place_of_settlement` / `alternative_settlement_system`, each with `source_published_at` and `effective_from` (publication ≠ go-live). |
| link topology | `link_topology` (collection) | Eurosystem CSD↔CSD links touching the issuer CSD — infrastructure context, never a route for this ISIN. |
| route assessments | `route_assessments` (collection) | `inferred`/`not_assessable` statements over the above; every entry carries `rule`, `limitations` and explicit conditions. |
