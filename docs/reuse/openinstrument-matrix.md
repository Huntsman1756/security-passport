# OpenInstrument reuse matrix

> Phase-0 audit of `Huntsman1756/openinstrument` (local sibling repo,
> v0.4.0, generation-0004, FIRDS snapshot 2026-10-03) against every
> Security Passport field. Decisions: **reuse** via the frozen
> REST contract, **extend** upstream (preferred to duplicating), or
> **new adapter** inside security-passport.

Verified contracts (live, `OPENINSTRUMENT_DATA=data/read`):

| Endpoint | Verified | Returns |
|---|---|---|
| `GET /v1/instruments/{isin}` | yes | canonical row: isin, cfi(+state), fisn(+state), full_name(+state), notional_currency(+state), issuer_lei(+state+assertion_count), competent_authority(+state), firds_snapshot, n_firds_records, cfi_letter |
| `GET /v1/instruments/{isin}/identifiers` | yes | FIGI rows by level (instrument/share_class/composite/venue) + provider |
| `GET /v1/instruments/{isin}/listings` | yes | venue_mic, relevant_venue, issuer_requested_admission, admission_approval_date, admission_request_date, first_trade_date, termination_date, locator — verbatim FIRDS datetimes, **sentinels unnormalized** |
| `GET /v1/instruments/{isin}/issuer` | yes | canonical_lei, state, per-provider assertions (gleif_isin_lei, firds_field5), GLEIF golden entity, GLEIF relationships |
| `GET /v1/instruments/{isin}/history` | yes | DLTINS events, publication-time semantics, left-censoring flag |
| `GET /v1/instruments/{isin}/as-of` | yes | point-in-time replay (baseline + ordered events) |
| `GET /v1/instruments/{isin}/evidence` | yes | artifact_sha256 + source_file + locator per provider |
| `GET /v2/instruments/{isin}` | yes | fund intelligence + `structured` block (G14 terms when present); **no generic debt-terms endpoint** — bond_terms only reachable via `structured` for the G13/G14 corpus |
| `GET /v2/instruments/{isin}/documents` | yes | fund document rows only |
| `GET /v1/search` | yes | exact ISIN/LEI/FIGI + text candidates |
| `GET /v1/status` | yes | versions + generation + attribution |

## Field decisions

| Passport field | Required semantics | OI surface | Sufficient? | Missing | Decision |
|---|---|---|---|---|---|
| isin / cfi / fisn | adjudicated FIRDS reference | `/v1/instruments` | yes | — | **reuse** |
| instrument name | best display name, verbatim evidence | `/v1/instruments` (full_name + state) | yes | — | **reuse** (FISN fallback) |
| notional currency | FIRDS NtnlCcy | `/v1/instruments` | yes | — | **reuse** |
| issuer LEI + state | adjudicated + conflicts preserved | `/v1/issuer` | yes | — | **reuse** |
| issuer name / entity | GLEIF golden entity | `/v1/issuer.entity` | yes | — | **reuse** |
| entity roles (fund vehicle vs mgmt co) | role-typed LEI assertions | `/v1/issuer` role is single `Issr` semantics; fund roles in `/v2` `roles[]` | partial | fund roles need `/v2` read | **reuse** `/v2` roles when present; else role=issuer only |
| maturity / debt terms | FIRDS DebtInstrmAttrbts | not in canonical row; only via debt corpus `/v2.structured` | no | FIRDS debt attrs not exported | **derive**: maturity from ECB row / PRIII when present; else `not_found` (v0.1). Extend upstream later. |
| venue listings | ISIN×MIC + segment + dates | `/v1/listings` | yes | sentinel normalization (ours) | **reuse** + own sentinel layer |
| venue lifecycle | derived state | none upstream | n/a | rule | **own rule** `venue_state.v1` over listing rows |
| first admission | derived, sentinel-safe | none upstream | n/a | rule | **own rule** `first_admission.v1` |
| FIRDS evidence refs | artifact+locator | `/v1/evidence` | yes | — | **reuse** as upstream evidence refs |
| publication history | DLTINS events | `/v1/history`, `/v1/as-of` | yes | — | **reuse** (v0.2 `--as-of` feeds) |
| prospectus document graph | PRIII parent/children/related | not served (raw responses local-only, corpus-bounded) | no | per-ISIN lookup service | **new adapter** `esma_prospectus` (ESMA Solr, documented M2M surface) |
| ECB eligibility | eligible + category + haircut inputs | not served; `intelligence/ecb_eligible` parquet local-only, corpus-bounded | no | API contract + history | **new adapter** `ecb_assets` (own bulk ingestion; spec assigns ECB to this repo) |
| issuer CSD | ECB `ISSUER_CSD` field | exists in OI parquet, not emitted upstream | no | not exported | **new adapter** (via own ECB ingestion) |
| ECB SSS eligibility | list of eligible SSSs | none | no | — | **new adapter** `ecb_sss` (HTML, observed history) |
| eligible links topology | investor→issuer SSS links | none | no | — | **new adapter** `ecb_sss` (HTML parse) |
| Iberclear instrument evidence | ISIN-specific admission | none | no | — | **v0.1**: ECB `issuer_csd` + ECB SSS/link evidence only; no invented admission |
| GLEIF ISIN→LEI | mapping assertions | `/v1/issuer` assertions | yes | — | **reuse** |
| MIC venue names | ISO 10383 | `mic.py` + `data/reference/iso10383` (local file, not API) | no | not served | **new adapter** `mic` (own public MIC CSV copy) |
| FIGI identifiers | level-typed | `/v1/identifiers` | yes | — | **reuse** |
| search | exact-first | `/v1/search` | yes | — | **reuse** (proxy) |
| settlement path | evidence-only assessment | none | n/a | — | **own rule** `settlement_path.v1` (conservative) |
| passport/adjudication | FACT/EVIDENCE/INFERENCE separation | OI does this internally for its own fields | n/a | — | **own** per-assertion projection over reused contracts |
| generations/atomic publish | build→validate→CURRENT | proven upstream, same author | pattern | — | **adopt pattern** (own implementation, smaller) |
| licensing projection | per-source servability | `licensing.py` upstream | pattern | — | **own registry** `docs/legal/` + source registry |

## Boundary

- Security Passport consumes OpenInstrument **only through the
  versioned REST API** (`OpenInstrumentApiProvider`). No Python
  imports, no parquet paths, no coupling to upstream internals.
- `FixtureInstrumentProvider` serves captured API payloads so the
  whole pipeline runs without OpenInstrument.
- An `OpenInstrumentDataRootProvider` (direct parquet) is **not**
  built in v0.1.0 — no performance case justifies it.
- Upstream gaps recorded for later: FIRDS debt attributes export,
  ECB parquet contract, generic `/v2` bond-terms endpoint.

## esma_data_py audit (mandatory prior art)

`European-Securities-Markets-Authority/esma_data_py`: EUPL-1.2,
last push 2025-11-24. Open issues confirm parsing fragility
(#5/#6 small-zip bug, #4 missing dataset types, #9 hardcoded
limit); PR #7 (FULCAN/DLTINS/FULINS parsing) unmerged. **Decision:
prior art only — not a dependency.** EUPL copyleft is incompatible
with copying into an MIT codebase; FIRDS is already served by
OpenInstrument, so no capability gap exists.
