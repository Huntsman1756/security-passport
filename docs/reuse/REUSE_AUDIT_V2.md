# REUSE AUDIT V2 — second pass (post-v0.1.0)

Audited: 2026-10-07. Repo pins are the local worktree HEADs verified
during this audit; licenses checked from each repo's own file.

Decision classes: `ADOPT` (runtime dependency), `WRAP` (adapter over a
live service/API), `PORT_SMALL_CODE` (copy with provenance note),
`PORT_PATTERN` (re-implement the concept, no code copied),
`REFERENCE` (prior art/semantic oracle only), `REJECT`, `CUSTOM`
(no adequate donor — genuine product logic).

## Owner repositories

| repo | local path / pin | license | capability audited | decision | reason |
|---|---|---|---|---|---|
| openinstrument | `openinstrument` sibling project @ `v0.4.0-18-gb6b5ace` | MIT | reference master, FIRDS history, GLEIF, artifacts store, ECB adapter, PRIII adapter, generations, API | **ADOPT (upstream service)** + **PORT_SMALL_CODE** for `artifacts/store.py` | Already pinned as upstream authority. The artifacts store is provider-agnostic and the exact gap in our `data/raw/`. |
| openbloomb (OpenVenue) | `openbloomb` sibling project @ `v0.2.0-21-gba7bc96` | MIT | `venues.py` MIC registry w/ operating↔segment reconciliation via registry's own OPERATING MIC column; rulebook family map; `/venues/{mic}`, `/instruments/{id}/operational-dossier`, `/instruments/{isin}/history`, `/rules/{sha256}` | **WRAP (optional provider)** + **REJECT our own MIC parser** | Runs offline from local data; distinguishes OPRT/SGMT correctly; rulebook corpus exists (`rules/registry.yaml`). Our 2,883-row MIC re-ingest duplicates it with less semantics. |
| posttrade-europe | `posttrade-europe` sibling project @ `d0f440a` | Apache-2.0 | `capture/` — blob store `sha256/hh/` + `RetrievalAttempt` (status/etag/last-modified/redirect chain, failures as data) + `BlobRecord` + `DiscoveryEdge` + hashed run manifests; CSD/SSS/T2S identity semantics | **PORT_PATTERN** now; **WRAP later** when gates stable | Self-declared experimental/pre-release — no runtime dep. But its capture discipline is strictly better than ours (attempts-as-data, redirect chains, response metadata). Pattern donor for our artifact layer. |
| emisiones-es | `emisiones-es` sibling project @ `p0-final-fail-4-gb14451e` | Apache-2.0 | CNMV acquisition, identity resolution, canonical model, document graph, conservative linkage | **WRAP (optional, validated parts only)** | P0 formally falsified its contractual extraction — do not re-enable. Acquisition/identity/document-graph passed their gates; usable as CNMV corroboration for ES instruments in v0.2. |
| OpenFunds (`cnmv_iic`) | `OpenFunds` sibling project @ `v0.1.0-2-gf538c3e` | MIT | CNMV fund registry: `Entidad(Gestora, Depositario)/Compartimento/Clase(ISIN)`; identity resolution `exact_share_class/exact_compartment/exact_fund/invalid/ambiguous` | **WRAP (optional provider)** | The authority for ES IIC roles — vehicle/manager/depositary. Never a replacement issuer LEI. v0.2 integration. |
| venue-rule-diff | `venue-rule-diff` sibling project @ `v0.1.0-2-gd50385f` | MIT | rulebook capture + PDF diff engine | **REFERENCE** (via OpenVenue rulebook refs) | Precomputed rulebook version/provenance only; never a per-request diff runtime. |
| OpenCNMV | `OpenCNMV` sibling project @ `g1-model-frozen-88-gb76073c` | MIT | CNMV issuer/entity reporting | **REJECT (runtime)** | Issuer reporting ≠ instrument passport; would blur scope. |
| corporate_actions | `corporate_actions` sibling project @ `v0.0.1-2-gd3e5e0b` | Apache-2.0 | lifecycle events | **REJECT (runtime)** / REFERENCE for vocabulary | Out of v0.2 scope. |
| finreg-es | `finreg-es` sibling project @ `v0.6.0-44-gf9878e72b` | MIT | ES regulatory corpus | **REJECT** | Regulatory text, not instrument evidence. |
| owership_radar | `owership_radar` sibling project @ `v0.1.0-alpha.2` | MIT | ownership | **REJECT** | Out of scope. |

## External OSS

| candidate | version | license | capability | decision | reason |
|---|---|---|---|---|---|
| `python-stdnum` | 2.2 | LGPL-2.1+ | ISIN (ISO 6166) + LEI (ISO 17442) validation incl. checksum | **ADOPT** | Our custom Luhn had a real parity bug (doubled wrong indices). stdnum is the reference implementation; LGPL obligations: dynamic linking is fine — we use it as a library, do not copy code, document in `docs/legal/attribution.md`. |
| `schemathesis` | latest | MIT | property-based API testing from OpenAPI | **ADOPT (CI)** | Detects 500s, schema mismatches, invalid-input acceptance without hand-written cases. |
| `oasdiff` | latest | Apache-2.0 | OpenAPI contract diff | **ADOPT (CI)** | Blocks unapproved breaking changes vs release baseline. |
| FINOS Common Domain Model | — | Apache-2.0 | reference model | **REFERENCE** | semantic nomenclature oracle only; no runtime dep for a 5-block passport. |
| OpenGamma Strata / QuantLib | — | Apache-2.0 / BSD | calc engines | **REFERENCE** | convention oracles; never providers. |
| FINOS secref-data | — | — | security reference | **REJECT** | archived project. |
| OpenFIGI / pygleif direct | — | — | live lookups | **REJECT** | OpenInstrument already integrates both as bulk evidence; live lookup would bypass its adjudication. |
| esma_data_py | — | EUPL-1.2 | FIRDS download/parse | **REJECT (runtime)** | FIRDS parsing is upstream-owned; prior art only. |

## Code eliminated / absorbed by reuse

| removed | replaced by | why |
|---|---|---|
| `domain/isin.py` custom Luhn checksum | `python-stdnum` isin/lei | parity bug found; reference impl exists |
| `providers/mic.py` ingest + MIC store | OpenVenue `/venues/{mic}` provider (optional) + ISO registry provenance | OpenVenue reconciles OPRT/SGMT correctly; third MIC implementation had less semantics |
| `data/raw/` normalized-payload pretending | artifact store ported from `openinstrument/artifacts/store.py` + posttrade capture discipline | byte-immutable, content-addressed, observation ledger |

## Duplications that remain (justified)

- **ECB eligible-assets adapter** — OpenInstrument has `ecb_ea.py`,
  but Security Passport needs haircut/absence semantics as
  passport-level *derived* fields with snapshot scoping; OI stores
  rows as assertions. Differential tests (FASE 14) gate drift.
- **PRIII normalization** — OI has a PRIII adapter for debt
  intelligence; ours normalizes the document graph to the passport
  shape. Same justification: different output contract.
- **ECB SSS/links parser** — no upstream equivalent exposes
  topology; stays own-source but moves onto the artifact store.

## Wrapped services (adapters, not code)

- `OpenInstrumentApiProvider` — upstream reference master.
- `VenueContextProvider` → `OpenVenueProvider` — optional;
  absence degrades MIC detail, never the passport.
- `PostTradeEvidenceProvider` — designed now, connected when
  posttrade-europe has a stable output contract; until then a thin
  direct adapter over official instrument-level artifacts.
- `FundRolesProvider` → OpenFunds (`cnmv_iic`) — optional, ES IIC.
- `CnmvDocsProvider` → emisiones-es — optional, ES issuance docs.

---

## Implemented decisions (v0.1.1)

The audit above became executable code. This section records what
actually shipped and the provenance of every port/adaptation.

### Adopted

- `python-stdnum>=2.2` — `domain/isin.py` is now a thin wrapper
  (`normalize`, `structural_ok`, `checksum_ok`, `valid`,
  `lei_ok`). The retired Luhn survives only as a differential
  test oracle in `tests/unit/test_isin_stdnum.py`. Stricter
  semantics adopted deliberately: real ISO 3166 issuance prefix
  required, so `XX…` ISINs reject. LGPL-2.1+ obligations recorded
  in `docs/legal/attribution.md` — library use, no copied code.
- `schemathesis>=4.0` (dev) — `tests/integration/
  test_schemathesis.py` runs generated cases over ASGI;
  `positive_data_acceptance` excluded (checksum rejection is
  intended behaviour, inexpressible in OpenAPI).
- `oasdiff` (CI binary) — `scripts/export_openapi.py` freezes
  `tests/fixtures/openapi-baseline.json`; CI runs
  `oasdiff breaking --fail-on ERR`.

### Ported (provenance)

- `evidence/store.py` — PORT_PATTERN of
  `openinstrument/src/openinstrument/artifacts/store.py`
  (`openinstrument@b6b5ace`, MIT) + `posttrade-europe/
  src/posttrade/capture/*` (`d0f440a`, Apache-2.0).
  Local differences: SHA-256 keyed blobs at
  `blobs/<hh>/<sha256>` (posttrade layout), `SourceArtifact`
  ledger keyed `(provider, source_family, period)` with
  `supersedes` (OI semantic), `RetrievalAttempt` records HTTP
  status/ETag/Last-Modified and failure classes — attempts are
  data even without a blob. `raw_state` values:
  `raw_available | normalized_only | upstream_artifact_reference`.
- `providers/venue_context.py` — the `VenueContextProvider` port
  + `FixtureVenueProvider` + `OpenVenueProvider` (thin HTTP) per
  the FASE-6 design; live wiring deferred to v0.2.

### New own-sources (allowed — official artifacts, no upstream
### equivalent exists at this grain)

- `providers/ecb_dictionary.py` — parses the ECB Eligible Assets
  Dictionary page into `stores/collateral_dictionary.json`
  (issuer CSD, asset type, issuer group, reference market
  codebooks). Corrected a real v0.1 defect: `CLBL01` had been
  labelled "CBL (Clearstream Banking Luxembourg)"; the official
  dictionary defines it as the JOINT "Euroclear Bank /
  Clearstream Banking S.A." ICSD code. The curated map in
  `providers/iberclear.py` is now a verbatim offline fallback of
  the dictionary, not an independent opinion.
- `providers/euronext_esmil.py` — parses the "ISINs eligible for
  settlement in Euronext Securities Milan" workbook (located via
  the posttrade-europe source catalog). Produces
  `post_trade.csd_admission` + `instrument_csd_evidence`
  collection — instrument-level CSD admission, reported.

### Upstream repair

- OpenInstrument `/v1/instruments/{isin}/evidence` — hardcoded
  `snapshot=2026-09-12` / `campaign=2026-09-26` → 503 on newer
  generations. Fixed upstream (`50e9677`): resolves the
  instrument's own `firds_snapshot` and the campaigns present;
  missing openfigi partitions degrade to empty evidence.
  Security Passport pins `MIN_OPENINSTRUMENT_COMMIT = "50e9677"`.

### Deferred by design

- OpenVenue live data bundle — port exists; waiting for a pinned
  service (v0.2).
- `emisiones-es` adapters — document graph only after its
  current gate cycle; extraction stays off.
- `OpenFunds` provider — ES IIC roles (v0.2); `fund_key/
  compartment_key/share_class_key` grain preserved.
- `--as-of` — ADR-005 temporal semantics incomplete.
- `corporate_actions`, `OpenCNMV`, `finreg-es`,
  `ownership-radar` — REJECT for runtime as audited.

## v0.1.2 — POST-TRADE model hardening + venue context

- `post_trade` re-modelled into four non-mergeable assertions:
  `issuer_csd` (ECB collateral-reference scope),
  `settlement_locations[]` (instrument-level, multi-CSD,
  publication≠effective), `link_topology[]` (infrastructure
  context), `route_assessments[]` (explicitly inferred).
  `csd_admission`/`possible_paths`/`relevant_links`/`issuer_sss`
  retired (pre-stable contract; noted in release notes).
- ESMIL workbook now parsed full-width: designated place
  (effective 2026-09-21) + alternative settlement systems +
  current place — formulas evaluated via `data_only`, never
  leaked as evidence.
- `euronext_frs` — second instrument-level file from the same
  European-offering docs page (FR registered shares).
- `euronext_porto_custody` — probed; ISIN-filterable page is
  `PUBLIC_HUMAN_LOOKUP` (CSV export endpoint 404s) — no crawler.
- Source registry gained the access taxonomy
  (`PUBLIC_MACHINE_READABLE` … `BLOCKED_POLICY`) with the
  hard no-scrape rule.
- Listings enriched with `operating_mic`/`oprt_sgmt`/`operator`/
  `operator_lei`/`market_category` from the same official ISO
  10383 registry OpenVenue wraps — `VenueContextProvider` remains
  the v0.2 boundary for the rulebook/dossier layer that the ISO
  file does not carry.

## v0.1.2b — OpenFunds wrapped; emisiones-es stays deferred

- `providers/openfunds.py` + `PassportStore.iic_roles` —
  cnmv_iic registry wrapped at the dataset boundary:
  `_load_openfunds_registry()` reads latest
  `share_classes`+`funds` period from `OPENFUNDS_DATASET` into
  `stores/fund_roles.json` (`upstream_artifact_reference`).
  Builder projects `fund_vehicle`, `fund_share_class`,
  `management_company`, `depositary` fields + `fund_roles`
  collection into `primary_market`. Roles are roles —
  gestora/depositario never become issuer identity, so a
  role-vs-issuer LEI difference is never a false conflict.
  Golden: `ES0105321030` (BBVA Eurostoxx 50 ETF — live ISIN
  present in both OI canonical and CNMV registry).
- `emisiones-es` — audited again: validated document-graph
  output is not yet a published machine-readable artifact
  (`.work/` is acquisition scratch; current product line is a
  human-facing browser). Stays WRAP-deferred until it exposes a
  stable bundle; its rejected extraction stack remains
  permanently off.
